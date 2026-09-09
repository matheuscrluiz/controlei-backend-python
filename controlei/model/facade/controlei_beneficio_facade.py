from datetime import date, datetime, timedelta
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_beneficio_dao import ControleiBeneficioDAO


def _normalizar_data(valor):
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip()[:10], '%Y-%m-%d').date()


def _competencia(valor):
    """YYYY-MM-DD qualquer -> 1º dia do mês (date)."""
    d = _normalizar_data(valor)
    return d.replace(day=1)


def _dias_ate_proxima_recarga(dia_recarga, hoje: date) -> int:
    """
    Dias até a próxima recarga. Se não há dia informado, até o fim do mês.
    Ex.: hoje 06/09, recarga dia 5 -> próxima é 05/10 -> 29 dias.
    """
    if not dia_recarga:
        prox_mes = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
        return max((prox_mes - hoje).days, 1)

    dia = int(dia_recarga)

    def _no_mes(ano, mes):
        # clamp: dia 31 num mês de 30 -> último dia do mês
        ultimo = ((date(ano, mes, 1) + timedelta(days=32)).replace(day=1)
                  - timedelta(days=1)).day
        return date(ano, mes, min(dia, ultimo))

    proxima = _no_mes(hoje.year, hoje.month)
    if proxima <= hoje:
        m = hoje.month + 1 if hoje.month < 12 else 1
        a = hoje.year if hoje.month < 12 else hoje.year + 1
        proxima = _no_mes(a, m)
    return max((proxima - hoje).days, 1)


class ControleiBeneficioFacade():
    """
    Benefícios — módulo APARTADO. Nada aqui interage com contas, cartões,
    categorias ou os derivados do núcleo (patrimônio/fluxo/projeção).
    """

    def __init__(self):
        self.dao = ControleiBeneficioDAO()

    # ---------------------- BENEFÍCIO ----------------------
    def listar(self, id_usuario: int):
        """Benefícios com saldo, gasto do mês e 'por dia' calculado."""
        rotina = 'listar'
        try:
            lista = convert_unique_dic_to_arrayDict(
                self.dao.get_beneficios(id_usuario))
            hoje = date.today()
            for b in lista:
                saldo = float(b.get('saldo') or 0)
                dias = _dias_ate_proxima_recarga(b.get('dia_recarga'), hoje)
                b['dias_ate_recarga'] = dias
                b['por_dia'] = round(saldo / dias, 2) if saldo > 0 else 0.0
            return lista
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar(self, parm_dict: dict):
        rotina = 'criar'
        try:
            id_beneficio = self.dao.insert_beneficio(parm_dict)
            self.dao.database_commit()
            return {'id_beneficio': id_beneficio}
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar(self, parm_dict: dict):
        rotina = 'atualizar'
        try:
            self.dao.update_beneficio(parm_dict)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar(self, id_beneficio: int):
        rotina = 'deletar'
        try:
            self.dao.delete_beneficio(id_beneficio)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    # ---------------------- MOVIMENTOS ----------------------
    def extrato(self, id_beneficio: int, competencia=None):
        """
        Extrato do mês + resumo (gastei/recebi no mês, saldo atual) +
        histórico de 6 meses + comparativo com o mês anterior.
        """
        rotina = 'extrato'
        try:
            comp = _competencia(
                competencia) if competencia else date.today().replace(day=1)
            movs = convert_unique_dic_to_arrayDict(
                self.dao.get_movimentos(id_beneficio, comp))
            resumo = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_mes(id_beneficio, comp))
            resumo = resumo[0] if resumo else {
                'gasto_mes': 0, 'recarga_mes': 0, 'saldo': 0}
            hist = convert_unique_dic_to_arrayDict(
                self.dao.get_historico_mensal(id_beneficio, 6))

            # comparativo: gasto do mês anterior ao selecionado
            mes_ant = (comp - timedelta(days=1)).replace(day=1)
            ant = convert_unique_dic_to_arrayDict(
                self.dao.get_resumo_mes(id_beneficio, mes_ant))
            gasto_ant = float(ant[0]['gasto_mes']) if ant else 0.0
            resumo['gasto_mes_anterior'] = gasto_ant
            resumo['variacao'] = float(
                resumo.get('gasto_mes') or 0) - gasto_ant

            return {
                'competencia': comp.isoformat(),
                'resumo': resumo,
                'movimentos': movs,
                'historico': hist,
            }
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def movimentar(self, parm_dict: dict):
        """Registra recarga (+) ou gasto (−). valor sempre positivo."""
        rotina = 'movimentar'
        try:
            tipo = (parm_dict.get('tipo') or '').lower()
            if tipo not in ('recarga', 'gasto'):
                raise ValueError("tipo deve ser 'recarga' ou 'gasto'")
            valor = float(parm_dict.get('valor') or 0)
            if valor <= 0:
                raise ValueError('valor deve ser maior que zero')

            self.dao.insert_movimento({
                'id_beneficio': parm_dict.get('id_beneficio'),
                'tipo': tipo,
                'valor': valor,
                'data': _normalizar_data(parm_dict.get('data')),
                'descricao': (parm_dict.get('descricao') or None),
            })
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_movimento(self, parm_dict: dict):
        rotina = 'atualizar_movimento'
        try:
            dados = dict(parm_dict)
            if dados.get('data'):
                dados['data'] = _normalizar_data(dados['data'])
            if dados.get('valor') is not None and float(dados['valor']) <= 0:
                raise ValueError('valor deve ser maior que zero')
            self.dao.update_movimento(dados)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_movimento(self, id_beneficio_mov: int):
        rotina = 'deletar_movimento'
        try:
            self.dao.delete_movimento(id_beneficio_mov)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
