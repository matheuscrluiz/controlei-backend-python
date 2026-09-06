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
