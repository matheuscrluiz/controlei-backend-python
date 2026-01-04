from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_instituicao_dao import ControleiInstituicaoDAO


class ControleiInstituicaoFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiInstituicaoDAO()

    def obter_instituicao(
        self,
        id_instituicao=None,

    ) -> dict:
        rotina = 'obter_instituicao'

        try:

            investimento = self.dao.get_bank(
                id_instituicao=id_instituicao)
            return convert_unique_dic_to_arrayDict(investimento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_instituicao(self, parm_dict: dict):
        rotina = 'criar_instituicao'

        try:

            id_instituicao = self.dao.insert_banks(parm_dict)
            self.dao.database_commit()

            return id_instituicao

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_instituicao(self, parm_dict: dict):
        rotina = 'atualizar_instituicao'

        try:

            self.dao.update_banks(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_instituicao(
            self,
            id_investimento: int,
    ):
        rotina = 'apagar_instituicao'

        try:

            self.dao.delete_banks(id_investimento)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
