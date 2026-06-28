"""
Ingestor de CSV para importação de fatura/extrato.

Sem dependências externas. Faz:
  - leitura robusta (encoding + separador),
  - assinatura do cabeçalho (para memorizar layout),
  - palpite automático de quais colunas são data/valor/descrição,
  - aplicação de um mapeamento -> formato canônico
        {id_externo: None, data (ISO), descricao, valor (com sinal)}.

A precisão não precisa ser perfeita: o preview com revisão é a rede de
segurança. Parsers de data e valor toleram os formatos brasileiros comuns.
"""
import csv
import io
import re
import hashlib
from datetime import datetime

_FORMATOS_DATA = (
    '%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y',
)


def _decodificar(conteudo_bytes: bytes) -> str:
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            return conteudo_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return conteudo_bytes.decode('utf-8', errors='ignore')


def _detectar_separador(texto: str) -> str:
    amostra = '\n'.join(texto.splitlines()[:10])
    try:
        return csv.Sniffer().sniff(amostra, delimiters=';,\t|').delimiter
    except csv.Error:
        # fallback: o que mais aparece na primeira linha
        primeira = amostra.splitlines()[0] if amostra else ''
        contagem = {d: primeira.count(d) for d in ';,\t|'}
        return max(contagem, key=contagem.get) or ','


def ler_csv(conteudo_bytes: bytes):
    """Devolve (colunas, linhas) — linhas é lista de listas (sem cabeçalho)."""
    texto = _decodificar(conteudo_bytes)
    sep = _detectar_separador(texto)
    leitor = csv.reader(io.StringIO(texto), delimiter=sep)
    linhas = [linha for linha in leitor if any(c.strip() for c in linha)]
    if not linhas:
        return [], []
    colunas = [c.strip() for c in linhas[0]]
    dados = linhas[1:]
    return colunas, dados


def assinatura(colunas) -> str:
    base = '|'.join(c.strip().lower() for c in colunas)
    return 'csv' + hashlib.sha1(base.encode('utf-8')).hexdigest()[:20]


def parse_data(valor: str):
    if not valor:
        return None
    s = valor.strip()[:10]
    for fmt in _FORMATOS_DATA:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_valor(valor: str):
    """Tolera 'R$ 1.234,56', '1234.56', '-12,30', '(12,30)' (negativo)."""
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None

    negativo = False
    if s.startswith('(') and s.endswith(')'):
        negativo = True
        s = s[1:-1]

    s = re.sub(r'[^\d,.\-]', '', s)  # remove R$, espaços, letras
    if not s or s in ('-', '.', ','):
        return None
    if '-' in s:
        negativo = True
        s = s.replace('-', '')

    if ',' in s and '.' in s:
        # o último separador é o decimal; o outro é milhar
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')

    try:
        n = float(s)
    except ValueError:
        return None
    return -n if negativo else n


def _coluna(linhas, idx):
    return [linha[idx] if idx < len(linha) else '' for linha in linhas]


def adivinhar_mapeamento(colunas, linhas, destino: str) -> dict:
    """Palpite das colunas por tipo de conteúdo. Devolve nomes de coluna."""
    amostra = linhas[:25]

    score_data, score_valor, score_texto = {}, {}, {}
    for i, nome in enumerate(colunas):
        vals = [v for v in _coluna(amostra, i)]
        nao_vazios = [v for v in vals if v.strip()] or ['']
        frac_data = sum(1 for v in nao_vazios if parse_data(v)) / len(
            nao_vazios)
        frac_valor = sum(1 for v in nao_vazios if parse_valor(v) is not None)\
            / len(nao_vazios)
        comp_medio = sum(len(v) for v in nao_vazios) / len(nao_vazios)
        score_data[nome] = frac_data
        score_valor[nome] = frac_valor
        score_texto[nome] = comp_medio

    col_data = max(score_data, key=score_data.get) if colunas else None
    if col_data and score_data[col_data] < 0.5:
        col_data = None

    # valor: melhor coluna numérica que não seja a de data
    candidatos_valor = {
        k: v for k, v in score_valor.items() if k != col_data}
    col_valor = (max(candidatos_valor, key=candidatos_valor.get)
                 if candidatos_valor else None)
    if col_valor and score_valor[col_valor] < 0.5:
        col_valor = None

    # descrição: coluna textual mais longa, fora data/valor
    candidatos_texto = {
        k: v for k, v in score_texto.items()
        if k not in (col_data, col_valor) and score_valor.get(k, 0) < 0.5}
    col_desc = (max(candidatos_texto, key=candidatos_texto.get)
                if candidatos_texto else None)

    return {
        'data': col_data,
        'valor': col_valor,
        'descricao': col_desc,
        # fatura: valores costumam vir positivos (gasto) -> inverter p/ compra.
        # extrato: valores já vêm com sinal (+entrada/-saída).
        'inverter_sinal': (destino == 'cartao'),
    }


def aplicar_mapeamento(colunas, linhas, mapeamento, destino: str) -> list:
    """Constrói a lista canônica a partir do mapeamento escolhido."""
    idx = {nome: i for i, nome in enumerate(colunas)}
    i_data = idx.get(mapeamento.get('data'))
    i_valor = idx.get(mapeamento.get('valor'))
    i_desc = idx.get(mapeamento.get('descricao'))
    inverter = bool(mapeamento.get('inverter_sinal'))

    canon = []
    for linha in linhas:
        data = parse_data(
            linha[i_data]) if i_data is not None and i_data < len(
            linha) else None
        valor = parse_valor(linha[i_valor]) if (
            i_valor is not None and i_valor < len(linha)) else None
        if data is None or valor is None:
            continue
        descricao = (linha[i_desc] if i_desc is not None and i_desc < len(
            linha) else '').strip()

        canon.append({
            'id_externo': None,
            'data': data,
            'descricao': descricao,
            'valor': -valor if inverter else valor,
        })
    return canon
