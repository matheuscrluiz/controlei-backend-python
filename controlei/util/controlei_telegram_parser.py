"""
Interpretador das mensagens do bot do Telegram.

A pessoa escreve COMO FALA e o bot extrai: intenção, valor, descrição,
destino (conta/cartão/benefício pelo nome) e data. Determinístico (regex +
heurística em português), sem IA paga, testável isoladamente.

Exemplos aceitos:
    "45 mercado"                 -> gasto 45, 'mercado', hoje
    "gastei 22,50 padaria ontem" -> gasto 22.50, 'padaria', ontem
    "recebi 3200 salário"        -> receita 3200
    "vale 22 padaria" / "va 22"  -> gasto no benefício VA
    "recarga 800 vale"           -> recarga no benefício
    "45 mercado no nubank"       -> destino 'nubank' (resolvido depois)
    "saldo" / "quanto tenho"     -> consulta saldo
    "quanto gastei" / "gastos"   -> consulta gastos do mês

Devolve um dict com:
    intencao : gasto | receita | beneficio_gasto | beneficio_recarga
             | consulta_saldo | consulta_gastos | ajuda | desconhecido
    valor    : float | None
    descricao: str
    destino  : str | None   (texto cru após "no/na/em", p/ match aproximado)
    data     : date
    erro     : str | None   (o que faltou, em linguagem de gente)
"""
import re
import unicodedata
from datetime import date, timedelta

# ---------- normalização ----------


def _sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def _norm(s: str) -> str:
    return re.sub(r'\s+', ' ', _sem_acento(s or '').lower().strip())


# ---------- vocabulário ----------
V_GASTO = ('gastei', 'gasto', 'paguei', 'comprei', 'compra', 'despesa', 'saiu')
V_RECEITA = ('recebi', 'receita', 'entrou', 'ganhei', 'caiu')
# coisas que SÃO receita mesmo sem verbo: "2100 de salário", "500 freela"
N_RECEITA = ('salario', 'salario', 'freela', 'freelance', 'reembolso', 'cashback',
             'decimo terceiro', '13o', 'ferias', 'bonus', 'comissao', 'dividendo',
             'dividendos', 'rendimento', 'rendimentos', 'aluguel recebido',
             'pix recebido', 'venda', 'vendi', 'pagamento recebido', 'restituicao')
V_RECARGA = ('recarga', 'recarreguei', 'recarregou', 'carregou', 'creditou')
# palavras que indicam benefício (VA/VR/VT) — o destino é o benefício
V_BENEFICIO = ('vale', 'va', 'vr', 'vt', 'beneficio', 'alimentacao', 'refeicao',
               'transporte', 'ticket', 'alelo', 'sodexo', 'pluxee', 'flash')
V_SALDO = ('saldo', 'quanto tenho', 'quanto eu tenho', 'tenho quanto')
V_GASTOS = ('quanto gastei', 'gastos', 'quanto ja gastei', 'gastei quanto',
            'resumo', 'como estou')
V_AJUDA = ('ajuda', 'help', '?', 'como usar', 'comandos')

# valor: 45 | 45,50 | 45.50 | 1.234,56 | R$ 45 | 45 reais
_VALOR_RE = re.compile(
    r'(?:r\$\s*)?(?<![\d,.])(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?)(?:\s*reais?)?(?![\d,.])')

# datas relativas e explícitas
_DIA_RE = re.compile(r'\bdia\s+(\d{1,2})\b')
_DATA_RE = re.compile(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b')
_RELATIVAS = {
    'hoje': 0, 'ontem': 1, 'anteontem': 2,
}

# destino: "no nubank", "na santander", "em dinheiro", "pelo cartao", "com o vale"
_DESTINO_RE = re.compile(
    r'\b(?:no|na|em|pelo|pela|com o|com a|do|da)\s+(.+?)$')


def _parse_valor(txt: str):
    m = _VALOR_RE.search(txt)
    if not m:
        return None, txt
    bruto = m.group(1)
    if ',' in bruto:
        num = float(bruto.replace('.', '').replace(',', '.'))
    elif bruto.count('.') == 1 and len(bruto.split('.')[1]) <= 2:
        num = float(bruto)            # 45.50
    else:
        num = float(bruto.replace('.', ''))  # 1.234
    # remove o trecho do valor (e R$/reais) do texto
    resto = (txt[:m.start()] + ' ' + txt[m.end():])
    return num, re.sub(r'\s+', ' ', resto).strip()


def _parse_data(txt: str, hoje: date):
    """Extrai a data e devolve (date, texto_sem_data)."""
    for palavra, delta in _RELATIVAS.items():
        if re.search(rf'\b{palavra}\b', txt):
            return hoje - timedelta(days=delta), re.sub(rf'\b{palavra}\b', ' ', txt)

    m = _DATA_RE.search(txt)
    if m:
        d, mth = int(m.group(1)), int(m.group(2))
        ano = hoje.year
        if m.group(3):
            a = int(m.group(3))
            ano = a + 2000 if a < 100 else a
        try:
            dt = date(ano, mth, d)
            # "05/10" digitado em setembro provavelmente é o passado, não
            # mês que vem — se ficou no futuro sem ano explícito, recua 1 ano
            if dt > hoje and not m.group(3):
                dt = date(ano - 1, mth, d)
            return dt, txt[:m.start()] + ' ' + txt[m.end():]
        except ValueError:
            pass

    m = _DIA_RE.search(txt)
    if m:
        d = int(m.group(1))
        if 1 <= d <= 31:
            # "dia 5": o dia 5 mais recente (este mês se já passou, senão o anterior)
            try:
                dt = hoje.replace(day=d)
            except ValueError:
                dt = None
            if dt is None or dt > hoje:
                mes_ant = (hoje.replace(day=1) - timedelta(days=1))
                try:
                    dt = mes_ant.replace(day=d)
                except ValueError:
                    dt = mes_ant
            return dt, txt[:m.start()] + ' ' + txt[m.end():]

    return hoje, txt


def _tem(txt: str, palavras) -> bool:
    return any(re.search(rf'\b{re.escape(p)}\b', txt) for p in palavras)


def _remover(txt: str, palavras) -> str:
    for p in palavras:
        txt = re.sub(rf'\b{re.escape(p)}\b', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


def interpretar(mensagem: str, hoje: date = None) -> dict:
    hoje = hoje or date.today()
    txt = _norm(mensagem)
    out = {'intencao': 'desconhecido', 'valor': None, 'descricao': '',
           'destino': None, 'data': hoje, 'erro': None, 'original': mensagem}

    if not txt:
        out['intencao'] = 'ajuda'
        return out

    # ---- consultas (sem valor) ----
    if _tem(txt, V_AJUDA) or txt in ('oi', 'ola', 'bom dia', 'boa tarde', 'boa noite'):
        out['intencao'] = 'ajuda'
        return out
    if _tem(txt, V_SALDO):
        if not _VALOR_RE.search(txt):
            out['intencao'] = 'consulta_saldo'
            return out
        # "saldo santander 107250,10" → CONCILIAÇÃO: informa o saldo real da
        # conta e o app registra a diferença (rendimento / ajuste)
        valor, resto = _parse_valor(_remover(txt, V_SALDO))
        resto = re.sub(r'^(do|da|de|no|na)\s+', '', resto).strip()
        out.update({'intencao': 'conciliar', 'valor': valor,
                   'destino': resto or None})
        return out
    if _tem(txt, V_GASTOS) and not _VALOR_RE.search(txt):
        out['intencao'] = 'consulta_gastos'
        return out

    # ---- registro ----
    eh_beneficio = _tem(txt, V_BENEFICIO)
    eh_recarga = _tem(txt, V_RECARGA)
    eh_receita = (_tem(txt, V_RECEITA) or _tem(
        txt, N_RECEITA)) and not eh_recarga
    # verbos saem da descrição
    txt = _remover(txt, V_GASTO + V_RECEITA + V_RECARGA)

    valor, txt = _parse_valor(txt)
    data, txt = _parse_data(txt, hoje)
    out['data'] = data

    # destino: "no nubank" etc. (fica por último na frase)
    destino = None
    m = _DESTINO_RE.search(txt)
    if m:
        destino = m.group(1).strip()
        txt = txt[:m.start()].strip()
    # o nome do benefício também é destino
    if eh_beneficio:
        for p in V_BENEFICIO:
            if re.search(rf'\b{p}\b', txt):
                destino = destino or p
        txt = _remover(txt, V_BENEFICIO)

    descricao = re.sub(r'^[\s\-–:,.]+|[\s\-–:,.]+$', '', txt)
    # preposição sobrando na frente ("de salario", "com uber", "pra mae")
    descricao = re.sub(
        r'^(de|do|da|dos|das|com|pra|para|pro|em|no|na)\s+', '', descricao)
    out['descricao'] = descricao
    out['destino'] = destino
    out['valor'] = valor

    if valor is None:
        out['erro'] = 'Não achei o valor. Ex.: "45 mercado".'
        return out

    if eh_beneficio:
        out['intencao'] = 'beneficio_recarga' if eh_recarga else 'beneficio_gasto'
    elif eh_recarga:
        # "recarga 800" sem dizer vale: assume benefício (recarga é coisa de vale)
        out['intencao'] = 'beneficio_recarga'
    elif eh_receita:
        out['intencao'] = 'receita'
    else:
        out['intencao'] = 'gasto'

    # descrição vazia fica vazia: o executor decide o fallback DEPOIS de
    # verificar se o "destino" era na verdade parte da descrição
    return out


TEXTO_AJUDA = (
    "Me manda como você fala 👇\n\n"
    "💸 <b>45 mercado</b> — gasto de R$ 45\n"
    "💰 <b>recebi 3200 salário</b> — receita\n"
    "🏦 <b>vale 22 padaria</b> — gasto no vale\n"
    "🔋 <b>recarga 800 vale</b> — recarga do vale\n"
    "📅 pode dizer <b>ontem</b>, <b>dia 5</b> ou <b>05/09</b>\n"
    "🏷 e onde foi: <b>no nubank</b>, <b>no débito</b>\n\n"
    "Consultas: <b>saldo</b> · <b>quanto gastei</b>\n"
    "🏦 <b>saldo nubank 1.250,40</b> — conferir saldo: o que o banco mostra vira rendimento/ajuste\n\n"
    "💡 Eu lembro em qual conta cada coisa caiu da última vez. "
    "Pra mudar, é só dizer uma vez: <b>salário no nubank</b>."
)
