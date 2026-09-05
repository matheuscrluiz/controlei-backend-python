"""
Extrai lançamentos de PDFs de fatura de cartão (Itaú, Banco do Brasil e
similares) para o preview de importação.

Estratégia (aprendida com PDFs reais):
  1) SEÇÕES — só aceitamos linhas dentro de seções de compras. Pagamentos,
     totais, encargos, limites e "próximas faturas" são ignorados por
     contexto, não por regex frágil.
  2) DUAS COLUNAS (Itaú) — o extract_text gruda as colunas lado a lado numa
     linha só ("Pagamentos efetuados Lançamentos: compras e saques"). Quando
     uma linha tem 2 datas + 2 valores, cortamos e tratamos como duas.
  3) SANIDADE — descartamos valor 0,00, linhas cujo texto é cabeçalho
     ("Total", "Vencimento", "Fechamento"...) e capturamos "02/12" como
     parcela (não como data).
  4) Pagamentos/créditos (valor negativo em seção de pagamento, "PGTO",
     "PAGAMENTO", "CASHBACK") saem como tipo 'credito' — o usuário decide
     no preview; não viram compra.
"""
import io
import re
from datetime import date

from .controlei_csv_ingestor import parse_valor

_DATA_RE = re.compile(r'\b(\d{2}/\d{2}(?:/\d{2,4})?)\b')
_VALOR_RE = re.compile(r'\(?-?\s*R?\$?\s*\d{1,3}(?:\.\d{3})*,\d{2}\)?-?')
_ANO_RE = re.compile(r'\b(20\d{2})\b')
# "02/12" colado a uma descrição = parcela atual/total (Itaú)
_PARCELA_RE = re.compile(r'\b(\d{2})/(\d{2})\b(?!/)')

# --- seções: o que abre "modo compra" e o que fecha ---
_ABRE_COMPRAS = (
    'lançamentos: compras e saques',
    'lancamentos: compras e saques',
    'lançamentos nesta fatura',
    'lancamentos nesta fatura',
    'lançamentos: produtos e serviços',   # anuidade etc. — é cobrança real
    'lancamentos: produtos e servicos',
)
_FECHA_COMPRAS = (
    'pagamentos efetuados',
    'compras parceladas - próximas faturas',
    'compras parceladas - proximas faturas',
    'encargos cobrados',
    'limites de crédito', 'limites de credito',
    'resumo da fatura',
    'total dos lançamentos', 'total dos lancamentos',
    'lançamentos no cartão', 'lancamentos no cartao',
    'total da fatura',
    'novo teto de juros',
    'simulação de compras', 'simulacao de compras',
    'fique atento',
)
# linhas que NUNCA são compra, mesmo dentro da seção
_LIXO = (
    'total', 'vencimento', 'fechamento', 'melhor data', 'emissão', 'emissao',
    'postagem', 'previsão', 'previsao', 'limite', 'saldo fatura', 'saldo financiado',
    'valor em r$', 'data estabelecimento', 'data descrição', 'data descricao',
    'juros', 'iof', 'multa', 'encargos',
)
# créditos/pagamentos (não são compra) — mesmo que apareçam na seção
_CREDITO = ('pgto', 'pagamento', 'cashback', 'estorno', 'crédito', 'credito',
            'redução', 'reducao', 'devolução', 'devolucao')


def _detectar_ano(texto: str) -> int:
    anos = [int(a) for a in _ANO_RE.findall(texto)]
    return max(anos) if anos else date.today().year


def _parse_data(token: str, ano: int):
    partes = token.split('/')
    try:
        if len(partes) == 3:
            a = int(partes[2])
            a = a + 2000 if a < 100 else a
            return date(a, int(partes[1]), int(partes[0]))
        return date(ano, int(partes[1]), int(partes[0]))
    except ValueError:
        return None


def _valor_com_sinal(bruto: str, linha: str):
    limpo = bruto.replace('R$', '').replace(' ', '')
    negativo = limpo.startswith('-') or limpo.endswith('-') or (
        limpo.startswith('(') and limpo.endswith(')'))
    limpo = limpo.strip('()-')
    try:
        v = parse_valor(limpo)
    except Exception:
        return None
    if v is None:
        return None
    return -abs(v) if negativo else abs(v)


def _eh_lixo(desc: str) -> bool:
    d = desc.lower().strip()
    if not d:
        return True
    return any(d.startswith(k) or d == k for k in _LIXO)


def _eh_credito(desc: str, valor: float) -> bool:
    d = desc.lower()
    return valor < 0 or any(k in d for k in _CREDITO)


def _split_colunas(s: str):
    """Itaú: 2 datas + 2 valores na mesma linha = 2 colunas grudadas.
    Corta na 2ª data. Se não der pra cortar com segurança, devolve inteira."""
    datas = list(_DATA_RE.finditer(s))
    valores = list(_VALOR_RE.finditer(s))
    if len(datas) >= 2 and len(valores) >= 2:
        corte = datas[1].start()
        esq, dir_ = s[:corte].strip(), s[corte:].strip()
        # cada metade precisa ter data E valor
        if _DATA_RE.search(esq) and _VALOR_RE.search(esq) and \
           _DATA_RE.search(dir_) and _VALOR_RE.search(dir_):
            return [esq, dir_]
    return [s]


def _extrair_parcela(desc: str):
    """'MEB FITNESSRIO 02/12' -> ('MEB FITNESSRIO', 2, 12).
    A parcela do Itaú vem no FIM da descrição (logo antes do valor). Um
    'nn/nn' no meio de texto longo é ruído da coluna direita — cortamos a
    descrição ali e não tratamos como parcela."""
    m = _PARCELA_RE.search(desc)
    if not m:
        return desc, None, None
    atual, total = int(m.group(1)), int(m.group(2))
    resto = desc[m.end():].strip()
    if resto:
        # há texto DEPOIS do nn/nn → não é parcela, é ruído: corta tudo dali
        return desc[:m.start()].strip(), None, None
    if 1 <= atual <= total <= 99:
        return desc[:m.start()].strip(), atual, total
    return desc[:m.start()].strip(), None, None


def _so_coluna_esquerda(s: str) -> str:
    """Itaú gruda a coluna direita (encargos/juros) após o valor da compra:
       '16/05 RGC CHOPP 18,00 Juros de mora 1,00 % am 0,00'
    A compra termina no PRIMEIRO valor monetário depois da data. Cortamos
    ali. Se a linha tiver 2 datas (2 compras lado a lado), não cortamos —
    o _split_colunas resolve."""
    datas = list(_DATA_RE.finditer(s))
    if len(datas) != 1:
        return s
    valores = list(_VALOR_RE.finditer(s))
    # primeiro valor após a data: a compra termina ali; o resto é ruído da
    # coluna direita (mesmo quando é só texto, sem valor)
    for v in valores:
        if v.start() > datas[0].end():
            return s[:v.end()]
    return s


def _heuristica_linhas(linhas, ano: int) -> list:
    itens = []
    em_compras = False
    for ln in linhas:
        raw = (ln or '').strip()
        if not raw:
            continue
        low = raw.lower()

        # --- máquina de seções ---
        # Só o INÍCIO da linha decide a seção (coluna esquerda). Marcadores
        # no meio da linha são a coluna direita do Itaú (encargos, juros) e
        # não devem fechar a seção de compras.
        abre = any(low.startswith(k) for k in _ABRE_COMPRAS)
        fecha = any(low.startswith(k) for k in _FECHA_COMPRAS)
        # Itaú p2: "Pagamentos efetuados Lançamentos: compras e saques" — a
        # esquerda é pagamento, a direita abre compras. Como a coluna
        # esquerda de pagamentos é curta (1 linha) e as compras dominam,
        # tratamos como abertura; o item de pagamento é filtrado por _CREDITO.
        if fecha and any(k in low for k in _ABRE_COMPRAS):
            abre, fecha = True, False
        if abre or fecha:
            em_compras = abre
            if not abre:
                continue
            # o cabeçalho pode vir grudado a uma compra (2 colunas); tira o
            # texto do cabeçalho e segue processando o que sobrou
            resto = raw
            for k in _ABRE_COMPRAS + _FECHA_COMPRAS:
                i = resto.lower().find(k)
                if i >= 0:
                    resto = resto[:i] + resto[i + len(k):]
            raw = resto.strip()
            if not _DATA_RE.search(raw):
                continue
        if not em_compras:
            continue

        for s in _split_colunas(_so_coluna_esquerda(raw)):
            datas = _DATA_RE.findall(s)
            valores = _VALOR_RE.findall(s)
            if not datas or not valores:
                continue

            bruto = valores[-1]
            valor = _valor_com_sinal(bruto, s)
            if valor is None or abs(valor) < 0.005:
                continue

            # descrição = linha sem a data (a 1ª) e sem o valor (o último)
            desc = s.replace(datas[0], ' ', 1)
            idx = desc.rfind(bruto)
            if idx >= 0:
                desc = desc[:idx] + ' ' + desc[idx + len(bruto):]
            desc = re.sub(r'\s+', ' ', desc).strip(' -|')
            desc = re.sub(r'\s+(BR|R\$|[DC])$', '', desc).strip()

            # ruído da coluna direita sem valor ("... Credito Rotativo /",
            # "... Os juros e encargos"): a descrição do banco é toda em
            # CAIXA ALTA/curta; um trecho que começa com palavra capitalizada
            # seguida de minúsculas longas após 20 chars é texto corrido.
            mruido = re.search(
                r'(?<=.{18})\s+(Credito Rotativo|Os juros|será cobrada|período|Simulação|Juros|Novo teto|Limite|Fique atento|Valor em)', desc)
            if mruido:
                desc = desc[:mruido.start()].strip()

            if _eh_lixo(desc):
                continue

            data = _parse_data(datas[0], ano)
            if not data:
                continue

            # pagamento da fatura anterior não é lançamento desta fatura
            if re.fullmatch(r'(pagamento|pgto\.?.*|total dos pagamentos)', desc.lower().strip()):
                continue

            desc, parc_atual, parc_total = _extrair_parcela(desc)
            tipo = 'credito' if _eh_credito(desc, valor) else 'compra'

            # confiança: linha limpa (1 data, 1 valor) = alta
            confianca = 'alta' if (len(valores) == 1 and len(datas) == 1
                                   and desc) else 'baixa'

            itens.append({
                'id_externo': None,
                'data': data,
                'descricao': desc,
                'valor': valor,
                'tipo': tipo,
                'parcela_atual': parc_atual,
                'parcela_total': parc_total,
                'confianca': confianca,
            })
    return itens


def _de_tabelas(pdf, ano: int) -> list:
    """Fallback: PDFs com tabela detectável e sem texto linha-a-linha."""
    itens = []
    for page in pdf.pages:
        for tabela in (page.extract_tables() or []):
            for row in tabela:
                celulas = [str(c or '').strip() for c in row]
                s = ' '.join(c for c in celulas if c)
                itens.extend(_heuristica_linhas(
                    ['lançamentos nesta fatura', s], ano))
    return itens


def extrair_de_pdf(conteudo_bytes, ano_padrao=None) -> list:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        textos = [(page.extract_text() or '') for page in pdf.pages]
        texto = '\n'.join(textos)
        ano = ano_padrao or _detectar_ano(texto)

        itens = _heuristica_linhas(texto.split('\n'), ano)
        if not itens:
            itens = _de_tabelas(pdf, ano)

    # dedup exato (Itaú repete "RGC CHOPP 18,00" duas vezes de verdade —
    # NÃO deduplicamos por descrição+valor; só descartamos linha idêntica
    # que veio de colunas grudadas mal cortadas)
    return itens
