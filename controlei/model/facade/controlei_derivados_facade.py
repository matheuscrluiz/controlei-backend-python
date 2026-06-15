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
