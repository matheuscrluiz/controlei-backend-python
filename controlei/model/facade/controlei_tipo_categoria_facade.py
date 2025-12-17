from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_tipo_categoria_dao import ControleiTipoCategoriaDAO


class ControleiTipoCategoriaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiTipoCategoriaDAO()

    def obter_tipo_categoria(self, id_tipo_categoria=None) -> dict:
        rotina = 'obter_tipo_categoria'

        try:

            categoria = self.dao.get_type_category(
                id_tipo_categoria=id_tipo_categoria)
            return convert_unique_dic_to_arrayDict(categoria)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_tipo_categoria(self, parm_dict: dict):
        rotina = 'criar_tipo_categoria'

        try:

            id_categoria = self.dao.insert_type_category(parm_dict)
            self.dao.database_commit()

            return id_categoria

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_tipo_categoria(self, parm_dict: dict):
        rotina = 'atualizar_tipo_categoria'

        try:
            if not parm_dict['id_tipo_categoria']:
                raise FacadeException(
                    __file__, rotina, 'ID do tipo da categoria é obrigatório')

            categoria = self.dao.get_type_category(
                id_tipo_categoria=parm_dict['id_tipo_categoria'])
            if not categoria:
                raise FacadeException(
                    __file__, rotina, 'Tipo da categoria não encontrado')

            self.dao.update_type_category(parm_dict)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
