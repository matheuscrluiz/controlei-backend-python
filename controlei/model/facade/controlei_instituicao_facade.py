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

            print('obtem_categoria: ', obtem_categoria)
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

            self.dao.delete_investment(id_investimento, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
