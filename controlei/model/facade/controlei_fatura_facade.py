import calendar
from datetime import date, datetime
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_fatura_dao import ControleiFaturaDAO
from ..dao.controlei_cartao_dao import ControleiCartaoDAO

STATUS_VALIDOS = ('aberta', 'fechada', 'paga')


def _data_no_mes(ano: int, mes: int, dia: int) -> date:
    """Monta a data no mês, limitando o dia ao último dia (ex.: 31 em fev)."""
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


def _proximo_mes(ano: int, mes: int):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _normalizar_competencia(competencia) -> date:
    """Aceita date ou string ('YYYY-MM' / 'YYYY-MM-DD')
      e devolve o 1º do mês."""
    if isinstance(competencia, date):
        return date(competencia.year, competencia.month, 1)
    texto = str(competencia).strip()
    for fmt in ('%Y-%m-%d', '%Y-%m'):
        try:
            d = datetime.strptime(texto, fmt).date()
            return date(d.year, d.month, 1)
        except ValueError:
            continue
    raise ValueError('Competência inválida (use YYYY-MM ou YYYY-MM-DD)')


class ControleiFaturaFacade():

    def __init__(self):
        """construtor da classe ControleiFaturaFacade"""
        self.dao = ControleiFaturaDAO()
        self.cartao_dao = ControleiCartaoDAO()

    def obter_fatura(
            self,
            id_fatura=None,
            id_cartao=None,
            status=None,
            competencia=None,
            id_usuario=None) -> dict:
        rotina = 'obter_fatura'

        try:
            if competencia:
                competencia = _normalizar_competencia(competencia)

            fatura = self.dao.get_fatura(
                id_fatura=id_fatura,
                id_cartao=id_cartao,
                status=status,
                competencia=competencia,
                id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(fatura)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_faturas_a_vencer(self, id_usuario, dias=7) -> dict:
        rotina = 'obter_faturas_a_vencer'

        try:
            d = int(dias) if dias is not None else 7
            return convert_unique_dic_to_arrayDict(
                self.dao.get_faturas_a_vencer(id_usuario=id_usuario, dias=d))

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def fechar_faturas_do_dia(self) -> dict:
        """Fecha (aberta -> fechada) as faturas cujo dia de fechamento já
        chegou. Idempotente: só toca em 'aberta'. Feito pra rodar no cron."""
        rotina = 'fechar_faturas_do_dia'

        try:
            ids = self.dao.get_ids_faturas_para_fechar()
            fechadas = 0
            for id_fatura in ids:
                self.dao.update_status_fatura(id_fatura, 'fechada')
                fechadas += 1
            if fechadas:
                self.dao.database_commit()
            return {'fechadas': fechadas}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_ou_criar_fatura(self, id_cartao: int, competencia) -> dict:
        """
        Acha a fatura do cartão naquela competência (mês de referência) ou cria
        uma nova, calculando fechamento/vencimento a partir dos dias do cartão.
        É o método que o fluxo de compra/parcela usa pra alocar cada parcela.
        """
        rotina = 'obter_ou_criar_fatura'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')

            competencia = _normalizar_competencia(competencia)

            # Já existe a fatura desse mês? Retorna ela.
            existente = self.dao.get_fatura(
                id_cartao=id_cartao, competencia=competencia)
            if existente:
                return existente[0]

            # Não existe: precisa dos dias do cartão pra calcular as datas.
            cartao = self.cartao_dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')
            cartao = cartao[0]

            dia_fechamento = cartao.get('dia_fechamento')
            dia_vencimento = cartao.get('dia_vencimento')
            if not dia_fechamento or not dia_vencimento:
                raise FacadeException(
                    __file__, rotina,
                    'Cartão sem dia de fechamento/vencimento (não é crédito?)')

            data_fechamento = _data_no_mes(
                competencia.year, competencia.month, int(dia_fechamento))

            # Vence depois de fechar: se o dia de vencimento é <= fechamento,
            # ele cai no mês seguinte.
            if int(dia_vencimento) <= int(dia_fechamento):
                vy, vm = _proximo_mes(competencia.year, competencia.month)
            else:
                vy, vm = competencia.year, competencia.month
            data_vencimento = _data_no_mes(vy, vm, int(dia_vencimento))

            id_fatura = self.dao.insert_fatura({
                'id_cartao': id_cartao,
                'competencia': competencia,
                'data_fechamento': data_fechamento,
                'data_vencimento': data_vencimento,
                'status': 'aberta',
            })
            self.dao.database_commit()

            return self.dao.get_fatura(id_fatura=id_fatura)[0]

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_total_fatura(self, id_fatura: int):
        """Retorna o total a pagar da fatura (parcelas + itens)."""
        rotina = 'obter_total_fatura'

        try:
            resultado = self.dao.get_total(id_fatura)
            if not resultado:
                return 0
            return resultado[0].get('valor') or 0

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_status_fatura(self, id_fatura: int, status: str):
        """Primitiva de status (aberta/fechada/paga). O 'pagar fatura' completo
        com a transferência que baixa o saldo — virá no fluxo de pagamento."""
        rotina = 'atualizar_status_fatura'

        try:
            if not id_fatura:
                raise FacadeException(
                    __file__, rotina, 'ID da fatura é obrigatório')

            status = (status or '').strip().lower()
            if status not in STATUS_VALIDOS:
                raise FacadeException(
                    __file__, rotina,
                    'Status inválido (use: aberta, fechada ou paga)')

            fatura = self.dao.get_fatura(id_fatura=id_fatura)
            if not fatura:
                raise FacadeException(
                    __file__, rotina, 'Fatura não encontrada')

            self.dao.update_status_fatura(id_fatura, status)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
