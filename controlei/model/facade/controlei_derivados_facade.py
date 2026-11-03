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
        "Resumo do mês": receitas e despesas por CATEGORIA, com itens, valor
        da referência lado a lado e destaques em frase.
          competencia : 'YYYY-MM'
          comparar    : 'anterior' | 'media' | 'YYYY-MM'

        Regras de leitura (pra não gerar alarme falso):
          * referência FRACA = mês com menos de 5 lançamentos, ou média com
            menos de 3 meses de dados → o front mostra os valores, mas sem
            percentual e sem alerta;
          * alerta "acima da média" só com 3+ meses anteriores com dados;
          * datas sempre em pt-BR ("agosto de 2026") — nunca 'YYYY-MM' em texto.
        """
        rotina = 'resumo_mes'
        try:
            from collections import defaultdict

            MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                     "agosto", "setembro", "outubro", "novembro", "dezembro"]

            def data_longa(k):           # 'YYYY-MM' -> 'agosto de 2026'
                return f"{MESES[int(k[5:7]) - 1]} de {k[:4]}"

            def brl(v):
                v = float(v or 0)
                return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            comp = competencia[:7]
            itens = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_mes_itens(id_usuario, comp))
            hist = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_grupos_meses(id_usuario, comp, 7))
            pos = convert_unique_dic_to_arrayDict(
                self.dao.get_posicao_mes(id_usuario, comp))
            pos = pos[0] if pos else {}

            # janela: o mês + 6 anteriores
            y, m = int(comp[:4]), int(comp[5:7])
            janela = []
            for i in range(6, -1, -1):
                mm, yy = m - i, y
                while mm <= 0:
                    mm += 12
                    yy -= 1
                janela.append(f"{yy:04d}-{mm:02d}")

            tot = defaultdict(float)       # (mes, nat, grupo) -> total
            tot_nat = defaultdict(float)   # (mes, nat) -> total
            qtd_mes = defaultdict(int)     # mes -> nº de lançamentos
            for h in hist:
                v = float(h['total'] or 0)
                tot[(h['competencia'], h['natureza'], h['grupo'])] += v
                tot_nat[(h['competencia'], h['natureza'])] += v
                qtd_mes[h['competencia']] += int(h.get('qtd') or 0)

            com_dados = {h['competencia'] for h in hist}
            anteriores = [mx for mx in janela[:-1] if mx in com_dados]

            # ---- referência ----
            if comparar == 'media':
                ref_codigo = 'media'
                ref_label = (f"média dos últimos {len(anteriores)} meses"
                             if anteriores else "média (sem meses anteriores)")
                ref_qtd = sum(qtd_mes[mx] for mx in anteriores)
                ref_fraca = len(anteriores) < 3

                def ref(nat, grupo=None):
                    vals = [(tot[(mx, nat, grupo)] if grupo else tot_nat[(mx, nat)])
                            for mx in anteriores]
                    return sum(vals) / len(vals) if vals else 0.0
            else:
                if comparar == 'anterior':
                    ref_codigo = anteriores[-1] if anteriores else janela[-2]
                else:
                    ref_codigo = comparar[:7]
                ref_label = data_longa(ref_codigo)
                ref_qtd = qtd_mes.get(ref_codigo, 0)
                ref_fraca = ref_qtd < 5

                def ref(nat, grupo=None):
                    return tot[(ref_codigo, nat, grupo)] if grupo else tot_nat[(ref_codigo, nat)]

            pode_media = len(anteriores) >= 3

            def media(nat, grupo):
                vals = [tot[(mx, nat, grupo)] for mx in anteriores]
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
                nomes = set(grupos[nat].keys())
                # categorias que existiam na referência e não neste mês também
                # aparecem (valor atual 0) — lado a lado fica completo
                if ref_codigo != 'media':
                    nomes |= {g for (mx, n, g) in tot if mx ==
                              ref_codigo and n == nat}
                else:
                    nomes |= {
                        g for (mx, n, g) in tot if mx in anteriores and n == nat}
                out = []
                for g in nomes:
                    its = sorted(grupos[nat].get(g, []),
                                 key=lambda x: x['data'], reverse=True)
                    total = sum(i['valor'] for i in its)
                    r = ref(nat, g)
                    md = media(nat, g) if pode_media else None
                    out.append({
                        'grupo': g, 'total': round(total, 2),
                        'referencia': round(r, 2), 'variacao': round(total - r, 2),
                        'media': round(md, 2) if md is not None else None,
                        'fixo': bool(its) and all(i['fixo'] for i in its),
                        'acima_media': bool(pode_media and md and total > md * 1.5),
                        'qtd': len(its),
                        'itens': its,
                    })
                out.sort(key=lambda x: (-x['total'], -x['referencia']))
                return out

            receitas = montar('receita')
            despesas = montar('despesa')
            R = sum(g['total'] for g in receitas)
            S = sum(g['total'] for g in despesas)
            rR, rS = ref('receita'), ref('despesa')
            fixo = sum(i['valor']
                       for g in despesas for i in g['itens'] if i['fixo'])
            res = R - S

            # ---- destaques (máx. 3, sem alarme quando a referência é fraca) ----
            dest = [{'tipo': 'up' if res >= 0 else 'down',
                     'texto': (f"Sobraram {brl(res)} em {data_longa(comp)}"
                               if res >= 0 else f"Faltaram {brl(abs(res))} em {data_longa(comp)}")
                     + (f" — você guardou {round(res / R * 100)}% do que entrou." if R > 0 and res >= 0 else ".")}]
            if ref_fraca:
                top = [g for g in despesas if g['total'] > 0][:2]
                if top:
                    dest.append({'tipo': 'info', 'texto': "Seus maiores gastos foram "
                                 + " e ".join(f"{g['grupo']} ({brl(g['total'])})" for g in top) + "."})
            else:
                muds = sorted((g for g in despesas if abs(g['variacao']) >= 0.01),
                              key=lambda g: -abs(g['variacao']))[:2]
                for g in muds:
                    mais = g['variacao'] > 0
                    dest.append({'tipo': 'down' if mais else 'up',
                                 'texto': f"{g['grupo']}: {brl(abs(g['variacao']))} a "
                                          f"{'mais' if mais else 'menos'} que em {ref_label}."})
                for g in despesas:
                    if g['acima_media'] and len(dest) < 3:
                        dest.append({'tipo': 'warn',
                                     'texto': f"{g['grupo']} está bem acima do seu normal: "
                                              f"{brl(g['total'])} contra média de {brl(g['media'])}."})

            # principal receita (ex.: "Salário" somando os dois lançamentos)
            principal = next((g for g in receitas if g['total'] > 0), None)

            return {
                'competencia': comp,
                'referencia': ref_codigo,          # 'YYYY-MM' ou 'media'
                'referencia_label': ref_label,     # já em pt-BR
                'referencia_fraca': ref_fraca,
                'referencia_qtd': ref_qtd,
                'meses_com_dados': sorted(com_dados),
                'totais': {
                    'receitas': round(R, 2), 'despesas': round(S, 2), 'resultado': round(res, 2),
                    'ref_receitas': round(rR, 2), 'ref_despesas': round(rS, 2),
                    'ref_resultado': round(rR - rS, 2),
                    'taxa_poupanca': round(res / R * 100, 1) if R > 0 else None,
                    'fixo': round(fixo, 2), 'variavel': round(S - fixo, 2),
                },
                'principal_receita': ({'grupo': principal['grupo'], 'total': principal['total'],
                                       'qtd': principal['qtd']} if principal else None),
                'receitas': receitas,
                'despesas': despesas,
                'posicao': {
                    'compras_credito': float(pos.get('compras_credito') or 0),
                    'faturas_pagas': float(pos.get('faturas_pagas') or 0),
                },
                'destaques': dest[:3],
            }
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def inicio_mes(self, id_usuario: int):
        """
        Tudo o que os cards novos do Início precisam, numa chamada:
          livre      : entradas do mês − já gasto − contas fixas ainda por vir
                       = livre pra gastar, e quanto dá por dia até o fim do mês
          ritmo      : gasto acumulado dia a dia (mês atual × anterior),
                       projeção no ritmo atual e teto total do orçamento
          categorias : gasto por categoria (atual × anterior)
          proximos   : próximos 30 dias — contas fixas (com valor ou "a definir"),
                       fechamento e vencimento de fatura
          cartoes    : limite, usado (faturas não pagas, incl. parcelas futuras)
                       e próxima fatura de cada cartão de crédito
        Visão "o que gastei": débito + compras no crédito pela data da compra.
        """
        rotina = 'inicio_mes'
        try:
            import calendar
            from datetime import date, timedelta
            from ..dao.controlei_orcamento_dao import ControleiOrcamentoDAO

            def d_(x):
                return date.fromisoformat(str(x)[:10]) if x is not None else None

            def f_(x):
                return float(x or 0)

            hoje = date.today()
            ini = hoje.replace(day=1)
            dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]
            fim = hoje.replace(day=dias_mes)
            fim_ant = ini - timedelta(days=1)
            ini_ant = fim_ant.replace(day=1)
            prox_ini = fim + timedelta(days=1)
            prox_fim = prox_ini.replace(
                day=calendar.monthrange(prox_ini.year, prox_ini.month)[1])
            janela_fim = hoje + timedelta(days=30)

            # ---------- ritmo ----------
            por_dia = {d_(r['data']): f_(r['total'])
                       for r in convert_unique_dic_to_arrayDict(
                           self.dao.get_gastos_por_dia(id_usuario, ini_ant, fim))}

            def acumulado(primeiro, ate_dia):
                out, soma = [], 0.0
                for k in range(ate_dia):
                    soma += por_dia.get(primeiro + timedelta(days=k), 0.0)
                    out.append(round(soma, 2))
                return out

            atual = acumulado(ini, hoje.day)
            anterior = acumulado(ini_ant, fim_ant.day)
            gasto_mes = atual[-1] if atual else 0.0
            projecao = round(gasto_mes / hoje.day * dias_mes,
                             2) if hoje.day >= 5 and gasto_mes else None
            anterior_mesmo_dia = anterior[min(
                hoje.day, len(anterior)) - 1] if anterior else 0.0

            efetivo = convert_unique_dic_to_arrayDict(
                ControleiOrcamentoDAO().get_efetivo(id_usuario, ini))
            orcamento_total = round(
                sum(f_(o['valor_teto']) for o in efetivo), 2)

            # ---------- livre pra gastar ----------
            e = convert_unique_dic_to_arrayDict(
                self.dao.get_entradas_e_previstos_mes(id_usuario, ini, fim))
            e = e[0] if e else {}
            entradas = f_(e.get('receitas_efetivadas')) + \
                f_(e.get('receitas_previstas'))
            ainda_sai = f_(e.get('despesas_previstas'))
            livre = round(entradas - gasto_mes - ainda_sai, 2)
            dias_restantes = dias_mes - hoje.day + 1

            # ---------- categorias ----------
            cats = {}
            comp_atual, comp_ant = ini.strftime(
                '%Y-%m'), ini_ant.strftime('%Y-%m')
            for r in convert_unique_dic_to_arrayDict(
                    self.dao.get_gastos_categoria_meses(id_usuario, ini_ant, fim)):
                c = cats.setdefault(
                    r['categoria'], {'categoria': r['categoria'], 'atual': 0.0, 'anterior': 0.0})
                if r['competencia'] == comp_atual:
                    c['atual'] += f_(r['total'])
                elif r['competencia'] == comp_ant:
                    c['anterior'] += f_(r['total'])
            categorias = sorted(
                cats.values(), key=lambda c: (-c['atual'], -c['anterior']))[:8]
            for c in categorias:
                c['atual'], c['anterior'] = round(
                    c['atual'], 2), round(c['anterior'], 2)

            # ---------- próximos dias ----------
            proximos = []
            ocorr = {}
            for o in convert_unique_dic_to_arrayDict(
                    self.dao.get_ocorrencias_recorrencia(id_usuario, ini, prox_fim)):
                ocorr.setdefault(
                    (int(o['id_recorrencia']), o['competencia']), []).append(o)
            for r in convert_unique_dic_to_arrayDict(self.dao.get_recorrencias_ativas(id_usuario)):
                for base in (ini, prox_ini):
                    ult = calendar.monthrange(base.year, base.month)[1]
                    dt = base.replace(day=min(int(r['dia_do_mes']), ult))
                    if not (hoje <= dt <= janela_fim):
                        continue
                    occ = ocorr.get(
                        (int(r['id_recorrencia']), base.strftime('%Y-%m')), [])
                    if any(o['status'] == 'efetivado' for o in occ):
                        continue          # já aconteceu
                    prev = [f_(o['valor']) for o in occ if o['status']
                            == 'previsto' and f_(o['valor']) > 0.005]
                    valor = prev[0] if prev else (
                        f_(r['valor']) if r.get('valor') is not None else None)
                    proximos.append({
                        'data': dt.isoformat(), 'tipo': 'recorrencia',
                        'descricao': r['dsc_recorrencia'], 'natureza': r['natureza'],
                        'valor': valor, 'origem': r.get('meio'),
                        'cartao': r.get('id_cartao') is not None,
                    })

            faturas = convert_unique_dic_to_arrayDict(
                self.dao.get_faturas_nao_pagas_valor(id_usuario))
            for fa in faturas:
                nome = f"{fa['cartao']}" + \
                    (f" ••{fa['ultimos4']}" if fa.get('ultimos4') else "")
                fecha, vence = d_(fa['data_fechamento']), d_(
                    fa['data_vencimento'])
                if fa['status'] == 'aberta' and fecha and hoje <= fecha <= janela_fim:
                    proximos.append({'data': fecha.isoformat(), 'tipo': 'fatura_fecha',
                                     'descricao': f"Fecha fatura {nome}", 'natureza': 'despesa',
                                     'valor': round(f_(fa['valor']), 2), 'origem': fa.get('instituicao'),
                                     'cartao': True})
                if vence and hoje <= vence <= janela_fim:
                    proximos.append({'data': vence.isoformat(), 'tipo': 'fatura_vence',
                                     'descricao': f"Vence fatura {nome}", 'natureza': 'despesa',
                                     'valor': round(f_(fa['valor']), 2), 'origem': fa.get('instituicao'),
                                     'cartao': True})
            proximos.sort(key=lambda x: (x['data'], x['tipo']))

            # ---------- cartões: limite usado ----------
            cartoes = []
            for ca in convert_unique_dic_to_arrayDict(self.dao.get_cartoes_credito(id_usuario)):
                fs = [fa for fa in faturas if int(
                    fa['id_cartao']) == int(ca['id_cartao'])]
                usado = round(sum(f_(fa['valor']) for fa in fs), 2)
                aberta = next((fa for fa in sorted(fs, key=lambda x: str(x['competencia']))
                               if fa['status'] == 'aberta'), None)
                limite = f_(ca['limite']) if ca.get(
                    'limite') is not None else None
                cartoes.append({
                    'id_cartao': int(ca['id_cartao']), 'apelido': ca['apelido'],
                    'ultimos4': ca.get('ultimos4'), 'instituicao': ca.get('instituicao'),
                    'limite': limite, 'usado': usado,
                    'disponivel': round(limite - usado, 2) if limite is not None else None,
                    'fatura_atual': round(f_(aberta['valor']), 2) if aberta else 0.0,
                    'fecha_em': str(aberta['data_fechamento'])[:10] if aberta else None,
                })

            return {
                'hoje': hoje.isoformat(), 'competencia': comp_atual,
                'competencia_anterior': comp_ant,
                'livre': {
                    'entradas': round(entradas, 2),
                    'entradas_recebidas': round(f_(e.get('receitas_efetivadas')), 2),
                    'gasto': round(gasto_mes, 2),
                    'ainda_vai_sair': round(ainda_sai, 2),
                    'previstos_sem_valor': int(e.get('previstos_sem_valor') or 0),
                    'livre': livre,
                    'dias_restantes': dias_restantes,
                    'por_dia': round(livre / dias_restantes, 2) if livre > 0 else 0.0,
                },
                'ritmo': {
                    'dias_mes': dias_mes, 'dias_mes_anterior': fim_ant.day,
                    'atual': atual, 'anterior': anterior,
                    'gasto_ate_hoje': round(gasto_mes, 2),
                    'anterior_mesmo_dia': round(anterior_mesmo_dia, 2),
                    'projecao_fim': projecao,
                    'orcamento_total': orcamento_total,
                },
                'categorias': categorias,
                'proximos': proximos[:8],
                'cartoes': cartoes,
            }
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def recentes(self, id_usuario: int, limite=15, offset=0):
        """Página de últimos registros: {itens, total} pra paginação."""
        rotina = 'recentes'
        try:
            itens = convert_unique_dic_to_arrayDict(
                self.dao.get_recentes(id_usuario, int(limite or 15), int(offset or 0)))
            total = int(itens[0]['total']) if itens else 0
            for i in itens:
                i.pop('total', None)
            return {'itens': itens, 'total': total}
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
