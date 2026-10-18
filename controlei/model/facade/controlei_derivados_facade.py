import json
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_derivados_dao import ControleiDerivadosDAO


class ControleiDerivadosFacade():

    def __init__(self):
        self.dao = ControleiDerivadosDAO()

    def saldo_conta(self, id_conta: int):
        rotina = 'saldo_conta'
        try:
            r = self.dao.get_saldo_conta(id_conta)
            return r[0].get('saldo') if r else 0
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def saldos_por_conta(self, id_usuario: int):
        rotina = 'saldos_por_conta'
        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_saldos_por_conta(id_usuario))
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def fatura_total(self, id_fatura: int):
        rotina = 'fatura_total'
        try:
            r = self.dao.get_fatura_total(id_fatura)
            return r[0].get('valor') if r else 0
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def divida_cartao(self, id_cartao=None, id_usuario=None):
        rotina = 'divida_cartao'
        try:
            r = self.dao.get_divida_cartao(
                id_cartao=id_cartao, id_usuario=id_usuario)
            return r[0].get('divida') if r else 0
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def registrar_snapshot(self, id_usuario: int):
        """Grava a posição de hoje (idempotente). Usado pelo dashboard ao
        carregar e pelo cron diário."""
        rotina = 'registrar_snapshot'
        try:
            self.dao.upsert_patrimonio_snapshot(id_usuario)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def registrar_snapshot_todos(self):
        """Cron diário: snapshot de todos os usuários."""
        rotina = 'registrar_snapshot_todos'
        try:
            ids = convert_unique_dic_to_arrayDict(self.dao.get_ids_usuarios())
            for u in ids:
                self.dao.upsert_patrimonio_snapshot(u['id_usuario'])
            self.dao.database_commit()
            return {'usuarios': len(ids)}
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def patrimonio_historico(self, id_usuario: int, dias=180):
        """
        Série + tendência: variação do patrimônio vs. ~30 dias atrás
        (o snapshot mais antigo dentro de 30 dias; se só há o de hoje, a
        tendência fica None — o front mostra sem variação).
        """
        rotina = 'patrimonio_historico'
        try:
            # garante que HOJE está na série antes de ler
            self.dao.upsert_patrimonio_snapshot(id_usuario)
            self.dao.database_commit()

            serie = convert_unique_dic_to_arrayDict(
                self.dao.get_patrimonio_historico(id_usuario, int(dias or 180)))

            tendencia = None
            if len(serie) >= 2:
                hoje = float(serie[-1]['patrimonio'] or 0)
                # ponto de referência: o mais próximo de 30 dias atrás
                from datetime import date, timedelta
                alvo = date.today() - timedelta(days=30)
                ref = min(
                    serie[:-1],
                    key=lambda x: abs((self._to_date(x['data']) - alvo).days))
                base = float(ref['patrimonio'] or 0)
                delta = hoje - base
                tendencia = {
                    'delta': delta,
                    'percentual': (delta / base * 100) if base else None,
                    'data_referencia': str(ref['data'])[:10],
                }

            return {'serie': serie, 'tendencia': tendencia}
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    @staticmethod
    def _to_date(v):
        from datetime import date, datetime
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        # string 'YYYY-MM-DD...' ou formato GMT do pandas
        s = str(v)
        try:
            return datetime.strptime(s[:10], '%Y-%m-%d').date()
        except ValueError:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(s).date()

    def cobertura_faturas(self, id_usuario: int):
        """Faturas cuja conta do cartão não tem saldo pra pagar."""
        rotina = 'cobertura_faturas'
        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_cobertura_faturas(id_usuario))
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def projecao(self, id_usuario: int):
        """Saldo projetado = atual + receitas prev. - despesas prev. - faturas."""
        rotina = 'projecao'
        try:
            dados = convert_unique_dic_to_arrayDict(
                self.dao.get_projecao(id_usuario))
            if dados:
                d = dados[0]
                # json_agg pode chegar já decodificado (lista) ou como texto,
                # conforme o driver — normaliza para lista
                for campo in ('recorrencias', 'faturas'):
                    v = d.get(campo)
                    if isinstance(v, str):
                        try:
                            d[campo] = json.loads(v)
                        except ValueError:
                            d[campo] = []
                    elif v is None:
                        d[campo] = []
                d['saldo_projetado'] = (
                    float(d.get('saldo_atual') or 0)
                    + float(d.get('receitas_previstas') or 0)
                    - float(d.get('despesas_previstas') or 0)
                    - float(d.get('faturas_a_vencer') or 0)
                )
            return dados
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def resumo_mes(self, id_usuario: int, competencia: str, comparar: str = 'anterior'):
        """
        "Resumo do mês" — árvore completa de um mês com comparação.
          competencia : 'YYYY-MM'
          comparar    : 'anterior' | 'media' | 'YYYY-MM'
        Devolve: totais, taxa de poupança, fixo×variável, pequenos gastos,
        grupos de receita e despesa (cada um com itens, referência, média 6m
        e série dos últimos 7 meses), posição de fechamento e destaques em
        frases. Toda a regra fica aqui — o front só apresenta.
        """
        rotina = 'resumo_mes'
        try:
            from collections import defaultdict
            from datetime import date as _date

            comp = competencia[:7]
            itens = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_mes_itens(id_usuario, comp))
            hist = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_grupos_meses(id_usuario, comp, 7))
            pos = convert_unique_dic_to_arrayDict(
                self.dao.get_posicao_mes(id_usuario, comp))
            pos = pos[0] if pos else {}

            # ---- meses da janela (7: o atual + 6 anteriores) ----
            y, m = int(comp[:4]), int(comp[5:7])
            meses = []
            for i in range(6, -1, -1):
                mm, yy = m - i, y
                while mm <= 0:
                    mm += 12
                    yy -= 1
                meses.append(f"{yy:04d}-{mm:02d}")
            # só meses COM MOVIMENTO entram na média — senão um usuário novo
            # teria a média derrubada por meses vazios e veria alertas falsos
            meses_com_dados = {h['competencia'] for h in hist}
            anteriores = [mx for mx in meses[:-1] if mx in meses_com_dados]

            # ---- totais por (mês, natureza, grupo) ----
            tot = defaultdict(float)          # (mes, nat, grupo) -> total
            tot_nat = defaultdict(float)      # (mes, nat) -> total
            for h in hist:
                k = (h['competencia'], h['natureza'], h['grupo'])
                tot[k] += float(h['total'] or 0)
                tot_nat[(h['competencia'], h['natureza'])
                        ] += float(h['total'] or 0)

            # ---- referência ----
            if comparar == 'media':
                ref_label = 'sua média (6 meses)'

                def ref(nat, grupo=None):
                    vals = [(tot[(mx, nat, grupo)] if grupo else tot_nat[(mx, nat)])
                            for mx in anteriores]
                    return sum(vals) / len(vals) if vals else 0.0
            else:
                ref_mes = (anteriores[-1] if comparar == 'anterior' and anteriores
                           else (comparar[:7] if comparar != 'anterior' else None))
                ref_label = ref_mes or 'sem mês anterior'

                def ref(nat, grupo=None):
                    if not ref_mes:
                        return 0.0
                    return tot[(ref_mes, nat, grupo)] if grupo else tot_nat[(ref_mes, nat)]

            def media(nat, grupo=None):
                vals = [(tot[(mx, nat, grupo)] if grupo else tot_nat[(mx, nat)])
                        for mx in anteriores]
                return sum(vals) / len(vals) if vals else 0.0

            # ---- árvore do mês ----
            grupos = {'receita': defaultdict(
                list), 'despesa': defaultdict(list)}
            for it in itens:
                grupos[it['natureza']][it['grupo']].append({
                    'fonte': it['fonte'], 'id_registro': int(it['id_registro']),
                    'descricao': it['descricao'], 'origem': it['origem'],
                    'data': str(it['data'])[:10], 'valor': float(it['valor'] or 0),
                    'fixo': bool(it['fixo']), 'credito': bool(it['credito']),
                    'categoria': it.get('categoria'),
                })

            def montar(nat):
                out = []
                for g, its in grupos[nat].items():
                    total = sum(i['valor'] for i in its)
                    r = ref(nat, g)
                    md = media(nat, g)
                    out.append({
                        'grupo': g, 'total': round(total, 2),
                        'referencia': round(r, 2), 'variacao': round(total - r, 2),
                        'media': round(md, 2),
                        'serie': [{'competencia': mx, 'total': round(tot[(mx, nat, g)], 2),
                                   'tem_dados': mx in meses_com_dados}
                                  for mx in meses],
                        'fixo': all(i['fixo'] for i in its),
                        'novo': r == 0 and total > 0,
                        'acima_media': bool(md > 0 and total > md * 1.5),
                        'itens': its,
                    })
                out.sort(key=lambda x: -x['total'])
                return out

            receitas = montar('receita')
            despesas = montar('despesa')
            R = sum(g['total'] for g in receitas)
            S = sum(g['total'] for g in despesas)
            rR, rS = ref('receita'), ref('despesa')
            fixo = sum(i['valor']
                       for g in despesas for i in g['itens'] if i['fixo'])
            pequenos = [i for g in despesas for i in g['itens']
                        if i['valor'] < 30]

            # grupos que existiam na referência e sumiram
            sumidos = []
            if comparar != 'media':
                for (mx, nat, g), v in tot.items():
                    if mx == ref_label and v > 0 and not grupos[nat].get(g):
                        sumidos.append(
                            {'natureza': nat, 'grupo': g, 'referencia': round(v, 2)})

            # ---- destaques (frases) ----
            def brl(v):
                v = float(v or 0)
                return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            res = R - S
            rres = rR - rS
            dest = []
            dest.append({'tipo': 'up' if res >= 0 else 'down',
                         'texto': (f"{'Sobrou' if res >= 0 else 'Faltou'} {brl(abs(res))}"
                                   + (f" — {'melhor' if res > rres else 'pior'} que {ref_label} ({brl(abs(rres))})." if rres else ".")
                                   + (f" Você guardou {round(res / R * 100)}% do que entrou." if R > 0 else ""))})
            muds = [(g, 'receita') for g in receitas] + \
                [(g, 'despesa') for g in despesas]
            muds = [m for m in muds if abs(m[0]['variacao']) > 0.005]
            muds.sort(key=lambda m: -abs(m[0]['variacao']))
            for g, nat in muds[:3]:
                good = g['variacao'] > 0 if nat == 'receita' else g['variacao'] < 0
                if g['novo']:
                    dest.append(
                        {'tipo': 'note', 'texto': f"{g['grupo']} apareceu: {brl(g['total'])} que não tinha em {ref_label}."})
                else:
                    pct = f" ({'+' if g['variacao'] > 0 else ''}{round(g['variacao'] / g['referencia'] * 100)}%)" if g['referencia'] else ""
                    dest.append({'tipo': 'up' if good else 'down',
                                 'texto': f"{g['grupo']} {'subiu' if g['variacao'] > 0 else 'caiu'} {brl(abs(g['variacao']))}{pct} vs. {ref_label}."})
            for g in despesas:
                if g['acima_media']:
                    dest.append(
                        {'tipo': 'note', 'texto': f"{g['grupo']} está {g['total'] / g['media']:.1f}× acima da sua média ({brl(g['total'])} vs. {brl(g['media'])})."})
            for sdo in sumidos[:1]:
                dest.append(
                    {'tipo': 'note', 'texto': f"{sdo['grupo']} sumiu: tinha {brl(sdo['referencia'])} em {ref_label}."})

            # ---- acumulado do ano ----
            ano = comp[:4]
            res_meses = {mx: tot_nat[(mx, 'receita')] - tot_nat[(mx, 'despesa')]
                         for mx in meses if mx.startswith(ano) and mx <= comp
                         and (mx in meses_com_dados or mx == comp)}
            melhor = max(res_meses, key=res_meses.get) if res_meses else None
            pior = min(res_meses, key=res_meses.get) if res_meses else None

            return {
                'competencia': comp, 'referencia_label': ref_label,
                'totais': {
                    'receitas': round(R, 2), 'despesas': round(S, 2), 'resultado': round(res, 2),
                    'ref_receitas': round(rR, 2), 'ref_despesas': round(rS, 2), 'ref_resultado': round(rres, 2),
                    'media_receitas': round(media('receita'), 2), 'media_despesas': round(media('despesa'), 2),
                    'taxa_poupanca': round(res / R * 100, 1) if R > 0 else None,
                    'fixo': round(fixo, 2), 'variavel': round(S - fixo, 2),
                    'pequenos_total': round(sum(i['valor'] for i in pequenos), 2),
                    'pequenos_qtd': len(pequenos),
                },
                'meses_com_dados': sorted(meses_com_dados),
                'serie_resultado': [{'competencia': mx, 'tem_dados': mx in meses_com_dados,
                                     'receitas': round(tot_nat[(mx, 'receita')], 2),
                                     'despesas': round(tot_nat[(mx, 'despesa')], 2),
                                     'resultado': round(tot_nat[(mx, 'receita')] - tot_nat[(mx, 'despesa')], 2)}
                                    for mx in meses],
                'receitas': receitas, 'despesas': despesas, 'sumidos': sumidos,
                'posicao': {
                    'patrimonio_inicio': pos.get('patrimonio_inicio'),
                    'patrimonio_fim': pos.get('patrimonio_fim'),
                    'faturas_pagas': float(pos.get('faturas_pagas') or 0),
                    'compras_credito': float(pos.get('compras_credito') or 0),
                },
                'ano': {'acumulado': round(sum(res_meses.values()), 2),
                        'melhor_mes': melhor, 'pior_mes': pior},
                'destaques': dest[:5],
            }
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def recentes(self, id_usuario: int, limite=15):
        rotina = 'recentes'
        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_recentes(id_usuario, int(limite or 15)))
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def fluxo_mensal(self, id_usuario: int, competencia=None):
        rotina = 'fluxo_mensal'
        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_fluxo_mensal(id_usuario, competencia))
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def cofre_valor(self, id_cofre: int):
        rotina = 'cofre_valor'
        try:
            r = self.dao.get_cofre_valor(id_cofre)
            return r[0].get('valor') if r else 0
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def patrimonio_usuario(self, id_usuario: int):
        rotina = 'patrimonio_usuario'
        try:
            r = self.dao.get_patrimonio_usuario(id_usuario)
            return r[0] if r else {
                'saldos': 0, 'cofres': 0, 'divida': 0, 'patrimonio': 0}
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def despesas_por_categoria(
            self, id_usuario: int, data_inicio: str, data_fim: str):
        rotina = 'despesas_por_categoria'
        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_despesas_por_categoria(
                    id_usuario, data_inicio, data_fim))
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
