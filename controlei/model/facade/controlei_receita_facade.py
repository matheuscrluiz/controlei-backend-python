from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_receita_dao import ControleiReceitaDAO
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiReceitaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiReceitaDAO()
        self.cat_dao = ControleiCategoriaDAO()
        self.user_dao = ControleiUserDAO()

    def obter_receita(self, id_receita=None, id_usuario=None) -> dict:
        rotina = 'obter_receita'

        try:

            receita = self.dao.get_income(
                id_receita=id_receita,
                id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(receita)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_receita(self, parm_dict: dict):
        rotina = 'criar_receita'

        try:
            tipos_categoria_aceito = ['Receita']
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
                    'tipo_categoria'] not in tipos_categoria_aceito:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O tipo da receita deve ser Receita"
                )

            id_receita = self.dao.insert_income(parm_dict)
            self.dao.database_commit()

            return id_receita

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_receita(self, parm_dict: dict):
        rotina = 'atualizar_receita'

        try:
            if not parm_dict.get('id_receita'):
                raise FacadeException(
                    __file__, rotina, 'ID da receita é obrigatório'
                )

            receita = self.dao.get_income(id_receita=parm_dict['id_receita'])
            if not receita:
                raise FacadeException(
                    __file__, rotina, 'Receita não encontrada'
                )

            tipos_categoria_aceito = ['Receita']
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

            if obtem_categoria[0][
                    'tipo_categoria'] not in tipos_categoria_aceito:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O tipo da categoria deve ser Receita"
                )

            self.dao.update_income(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_receita(
            self,
            id_receita: int,
            id_usuario: int
    ):
        rotina = 'apagar_receita'

        try:
            if not id_receita:
                raise FacadeException(
                    __file__, rotina, 'ID da receita é obrigatório'
                )

            receita = self.dao.get_income(id_receita=id_receita)
            if not receita:
                raise FacadeException(
                    __file__, rotina, 'Receita não encontrada'
                )

            usuario = self.user_dao.get_user_by_id(
                id_usuario=id_usuario)

            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado'
                )
            if usuario['id_usuario'] != id_usuario:
                raise FacadeException(
                    __file__,
                    rotina,
                    'Você não tem permissão para deletar esta receita'
                )

            self.dao.delete_income(id_receita, id_usuario)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
