"""
Ingestor de PDF para importação de fatura/extrato.

Estratégia (0800):
  1) extrai o texto com pdfplumber e aplica uma heurística de linha:
     toda linha que tem uma DATA e um VALOR monetário é uma transação;
  2) se a heurística não achar nada, tenta as tabelas do pdfplumber.

Cada item recebe um nível de 'confianca' ('alta'/'baixa') para o usuário
focar a revisão. O preview continua sendo a rede de segurança — PDF é
inerentemente menos confiável que OFX/CSV.

Saída: lista canônica {id_externo: None, data (ISO), descricao,
valor (com sinal), confianca}.

Requer a dependência 'pdfplumber' (importada de forma lazy pelo facade).
"""
import io
import re
from datetime import datetime, date

from .controlei_csv_ingestor import parse_valor

_DATA_RE = re.compile(r'\b(\d{2}/\d{2}(?:/\d{2,4})?)\b')
_VALOR_RE = re.compile(
    r'\(?-?\s*R?\$?\s*\d{1,3}(?:\.\d{3})*,\d{2}\)?-?')
_ANO_RE = re.compile(r'\b(20\d{2})\b')


def _detectar_ano(texto: str) -> int:
    m = _ANO_RE.search(texto or '')
    return int(m.group(1)) if m else date.today().year


def _parse_data(token: str, ano: int):
    t = token.strip()
    try:
        if len(t) <= 5:  # dd/mm
            return date(ano, int(t[3:5]), int(t[0:2])).isoformat()
        for fmt in ('%d/%m/%Y', '%d/%m/%y'):
            try:
                return datetime.strptime(t, fmt).date().isoformat()
            except ValueError:
                continue
    except (ValueError, IndexError):
        return None
    return None


def _valor_com_sinal(bruto: str, linha: str):
    v = parse_valor(bruto)
    if v is None:
        return None
    # marcador D/C logo após o valor (comum no Banco do Brasil)
    m = re.search(re.escape(bruto.strip()) + r'\s*([DC])\b', linha)
    if m:
        return -abs(v) if m.group(1) == 'D' else abs(v)
    return v


def _heuristica_linhas(linhas, ano: int) -> list:
    itens = []
    for ln in linhas:
        s = (ln or '').strip()
        if not s:
            continue
        datas = _DATA_RE.findall(s)
        valores = _VALOR_RE.findall(s)
        if not datas or not valores:
            continue

        data = _parse_data(datas[0], ano)
        if not data:
            continue

        bruto = valores[-1]
        valor = _valor_com_sinal(bruto, s)
        if valor is None:
            continue

        desc = s.replace(datas[0], ' ', 1).replace(bruto, ' ')
        desc = re.sub(r'\s+', ' ', desc).strip(' -|')
        desc = re.sub(r'\s+[DC]$', '', desc).strip()

        # confiança: 1 valor e 1 data na linha = limpo; mais que isso = dúbio
        confianca = 'alta' if (
            len(valores) == 1 and len(datas) == 1 and desc) else 'baixa'

        itens.append({
            'id_externo': None,
            'data': data,
            'descricao': desc,
            'valor': valor,
            'confianca': confianca,
        })
    return itens


def _de_tabelas(pdf, ano: int) -> list:
    """Reserva: varre tabelas e pega a 1ª data + último valor de cada linha."""
    itens = []
    for page in pdf.pages:
        for tabela in (page.extract_tables() or []):
            for linha in tabela:
                celulas = [c for c in (linha or []) if c]
                texto = ' '.join(str(c) for c in celulas)
                datas = _DATA_RE.findall(texto)
                valores = _VALOR_RE.findall(texto)
                if not datas or not valores:
                    continue
                data = _parse_data(datas[0], ano)
                valor = _valor_com_sinal(valores[-1], texto)
                if not data or valor is None:
                    continue
                desc = texto.replace(datas[0], ' ', 1).replace(
                    valores[-1], ' ')
                desc = re.sub(r'\s+', ' ', desc).strip(' -|')
                desc = re.sub(r'\s+[DC]$', '', desc).strip()
                itens.append({
                    'id_externo': None,
                    'data': data,
                    'descricao': desc,
                    'valor': valor,
                    'confianca': 'baixa',
                })
    return itens


def extrair_de_pdf(conteudo_bytes, ano_padrao=None) -> list:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        textos = []
        for page in pdf.pages:
            textos.append(page.extract_text() or '')
        texto = '\n'.join(textos)
        ano = ano_padrao or _detectar_ano(texto)

        itens = _heuristica_linhas(texto.split('\n'), ano)
        if not itens:
            itens = _de_tabelas(pdf, ano)

    return itens
