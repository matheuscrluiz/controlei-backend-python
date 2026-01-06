from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_investimento_dao import ControleiInvestimentoDAO
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO
from ..dao.controlei_aporte_investimento_dao import (
    ControleiAporteInvestimentoDAO)


class ControleiInvestimentoFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiInvestimentoDAO()
        self.cat_dao = ControleiCategoriaDAO()
        self.user_dao = ControleiUserDAO()
        self.ap_dao = ControleiAporteInvestimentoDAO()

    def obter_investimento(
        self,
        id_investimento=None,
        ch_rede=None,

    ) -> dict:
        rotina = 'obter_investimento'

        try:
            ch_rede = ch_rede.upper()
            investimento = self.dao.get_investment(
                id_investimento=id_investimento,
                ch_rede=ch_rede)
            return convert_unique_dic_to_arrayDict(investimento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_investimento(self, parm_dict: dict):
        rotina = 'criar_investimento'

        try:
            obtem_categoria = convert_unique_dic_to_arrayDict(
                self.cat_dao.get_category(
                    id_categoria=parm_dict['id_categoria']
                ))

            if not obtem_categoria:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Categoria não encontrada!"
                )

            if obtem_categoria[0][
                    'codigo_tipo_categoria'] != 'Investimentos':
                raise FacadeException(
                    __file__,
                    rotina,
                    "A categoria deve ser do tipo investimento"
                )

            if parm_dict['valor_inicial'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da investimento não pode ser menor que zero"
                )

            id_investimento = self.dao.insert_investment(parm_dict)
            self.dao.database_commit()

            return id_investimento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_investimento(self, parm_dict: dict):
        rotina = 'atualizar_investimento'

        try:
            if not parm_dict.get('id_investimento'):
                raise FacadeException(
                    __file__, rotina, 'ID da investimento é obrigatório'
                )

            investimento = self.dao.get_investment(
                id_investimento=parm_dict['id_investimento'],
                ch_rede=parm_dict['ch_rede'])
            if not investimento:
                raise FacadeException(
                    __file__, rotina, 'investimento não encontrada'
                )

            obtem_categoria = convert_unique_dic_to_arrayDict(
                self.cat_dao.get_category(
                    id_categoria=parm_dict['id_categoria']
                )
            )

            if not obtem_categoria:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Categoria não encontrada!"
                )

            if parm_dict['valor_inicial'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da investimento não pode ser menor que zero"
                )

            self.dao.update_investment(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_investimento(
            self,
            id_investimento: int,
            ch_rede: str
    ):
        rotina = 'apagar_investimento'

        try:
            if not id_investimento:
                raise FacadeException(
                    __file__, rotina, 'ID da investimento é obrigatório'
                )

            investimento = self.dao.get_investment(
                id_investimento=id_investimento,
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

            aportes = self.ap_dao.get_investment_injection(
                id_investimento=id_investimento,
                ch_rede=ch_rede
            )

            if aportes:
                for aporte in aportes:
                    self.ap_dao.delete_investment_injection(
                        id_aporte=aporte['id_aporte']
                    )

            self.ap_dao.database_commit()
            self.dao.delete_investment(id_investimento, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
