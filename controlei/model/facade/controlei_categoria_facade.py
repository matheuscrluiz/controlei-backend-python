from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO


class ControleiCategoriaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiCategoriaDAO()

    def obter_categoria(self, id_categoria=None) -> dict:
        rotina = 'obter_categoria'

        try:

            categoria = self.dao.get_category(id_categoria=id_categoria)
            return convert_unique_dic_to_arrayDict(categoria)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_categoria(self, parm_dict: dict):
        rotina = 'criar_categoria'

        try:
            tipos_categoria_aceito = ['Receita', 'Despesa']
            if parm_dict['tipo_categoria'] not in tipos_categoria_aceito:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O tipo da categoria deve ser Receita ou Despesa"
                )

            id_categoria = self.dao.insert_categoria(parm_dict)
            self.dao.database_commit()

            return id_categoria

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_categoria(self, parm_dict: dict):
        rotina = 'atualizar_categoria'

        try:
            if not parm_dict['id_categoria']:
                raise FacadeException(
                    __file__, rotina, 'ID da categoria é obrigatório')

            # Verificar se usuário existe
            categoria = self.dao.get_category(
                id_categoria=parm_dict['id_categoria'])
            if not categoria:
                raise FacadeException(
                    __file__, rotina, 'Categoria não encontrado')

            tipos_categoria_aceito = ['Receita', 'Despesa']
            if parm_dict['tipo_categoria'] not in tipos_categoria_aceito:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O tipo da categoria deve ser Receita ou Despesa"
                )

            self.dao.update_categoria(parm_dict)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
