"""
Parser OFX mínimo e sem dependências externas.

Cobre OFX 1.x (SGML, tags de folha não fechadas) e OFX 2.x (XML),
porque extraímos os campos por regex dentro de cada bloco <STMTTRN>.

Saída: lista de dicts {fitid, data (ISO), descricao, valor (com sinal), trntype}.
"""
import re
from datetime import date


def _decodificar(conteudo_bytes: bytes) -> str:
    for enc in ('utf-8', 'latin-1', 'cp1252'):
        try:
            return conteudo_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return conteudo_bytes.decode('utf-8', errors='ignore')


def _tag(bloco: str, nome: str):
    # captura até o fim da linha ou o próximo '<' (serve p/ SGML e XML)
    m = re.search(rf'<{nome}>([^<\r\n]*)', bloco, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_data(raw: str) -> str:
    # DTPOSTED ex.: 20260115 ou 20260115120000[-3:GMT]
    d = raw.strip()[:8]
    return date(int(d[0:4]), int(d[4:6]), int(d[6:8])).isoformat()


def parse_ofx(conteudo) -> list:
    texto = conteudo if isinstance(conteudo, str) else _decodificar(conteudo)

    transacoes = []
    blocos = re.findall(
        r'<STMTTRN>(.*?)</STMTTRN>', texto, re.DOTALL | re.IGNORECASE)

    for b in blocos:
        dtposted = _tag(b, 'DTPOSTED')
        trnamt = _tag(b, 'TRNAMT')
        if not dtposted or trnamt is None:
            continue

        descricao = _tag(b, 'MEMO') or _tag(b, 'NAME') or ''
        try:
            valor = float(trnamt.replace(',', '.'))
        except ValueError:
            continue

        transacoes.append({
            'fitid': _tag(b, 'FITID'),
            'data': _parse_data(dtposted),
            'descricao': descricao.strip(),
            'valor': valor,
            'trntype': (_tag(b, 'TRNTYPE') or '').upper(),
        })

    return transacoes
