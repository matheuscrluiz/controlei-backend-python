from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_aporte_investimento_dao import (
    ControleiAporteInvestimentoDAO)
from ..dao.controlei_investimento_dao import ControleiInvestimentoDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiAporteInvestimentoFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiAporteInvestimentoDAO()
        self.inv_dao = ControleiInvestimentoDAO()
        self.user_dao = ControleiUserDAO()

    def obter_aporte_investimento(
        self,
        id_aporte=None,
        id_investimento=None,
        ch_rede=None,

    ) -> dict:
        rotina = 'obter_aporte_investimento'

        try:

            investimento = self.dao.get_investment_injection(
                id_aporte=id_aporte,
                id_investimento=id_investimento,
                ch_rede=ch_rede)
            return convert_unique_dic_to_arrayDict(investimento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_aporte_investimento(self, parm_dict: dict):
        rotina = 'criar_aporte_investimento'

        try:
            obtem_investimento = \
                self.inv_dao.get_investment(
                    id_investimento=parm_dict['id_investimento'],
                    ch_rede=parm_dict['ch_rede'],
                )

            if not obtem_investimento:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Investimento não encontrado!"
                )

            if obtem_investimento[0][
                    'ch_rede'] != parm_dict['ch_rede']:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Somente o criador do investimento pode fazer aporte"
                )

            if parm_dict['valor_aporte'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor do aporte não pode ser menor que zero"
                )

            id_investimento = self.dao.insert_investment_injection(parm_dict)
            self.dao.database_commit()

            return id_investimento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_aporte_investimento(self, parm_dict: dict):
        rotina = 'atualizar_aporte_investimento'

        try:
            if not parm_dict.get('id_investimento'):
                raise FacadeException(
                    __file__, rotina, 'ID da investimento é obrigatório'
                )

            aporte = self.dao.get_investment_injection(
                id_aporte=parm_dict['id_aporte'],
                ch_rede=parm_dict['ch_rede'])
            if not aporte:
                raise FacadeException(
                    __file__, rotina, 'aporte não encontrado'
                )

            if parm_dict['valor_aporte'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor do aporte não pode ser menor que zero"
                )

            self.dao.update_investment_injection(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_aporte_investimento(
            self,
            id_aporte: int,
            ch_rede: str
    ):
        rotina = 'apagar_aporte_investimento'

        try:
            if not id_aporte:
                raise FacadeException(
                    __file__, rotina, 'ID da investimento é obrigatório'
                )

            investimento = self.dao.get_investment_injection(
                id_aporte=id_aporte,
                ch_rede=ch_rede)
            if not investimento:
                raise FacadeException(
                    __file__, rotina, 'investimento não encontrada'
                )

            usuario = self.user_dao.get_user(
                ch_rede=ch_rede)

            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado'
                )
            if usuario[0]['ch_rede'] != ch_rede:
                raise FacadeException(
                    __file__,
                    rotina,
                    'Você não tem permissão para deletar esta investimento'
                )

            self.dao.delete_investment_injection(id_aporte)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
