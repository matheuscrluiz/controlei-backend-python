from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO


class ControleiCategoriaFacade():

    def __init__(self):
        """construtor da classe ControleiCategoriaFacade"""
        self.dao = ControleiCategoriaDAO()

    def obter_categoria(
            self,
            id_categoria=None,
            id_tipo_categoria=None,
            id_usuario=None) -> dict:
        rotina = 'obter_categoria'

        try:
            categoria = self.dao.get_category(
                id_categoria=id_categoria,
                id_tipo_categoria=id_tipo_categoria,
                id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(categoria)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_categoria(self, parm_dict: dict):
        rotina = 'criar_categoria'

        try:
            id_usuario = parm_dict.get('id_usuario')
            dsc_categoria = (parm_dict.get('dsc_categoria') or '').strip()
            id_tipo_categoria = parm_dict.get('id_tipo_categoria')

            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')
            if not dsc_categoria:
                raise FacadeException(
                    __file__, rotina, 'Descrição da categoria é obrigatória')
            if not id_tipo_categoria:
                raise FacadeException(
                    __file__, rotina, 'Tipo da categoria é obrigatório')

            parms = {
                'id_usuario': id_usuario,
                'dsc_categoria': dsc_categoria,
                'id_tipo_categoria': id_tipo_categoria,
            }

            id_categoria = self.dao.insert_categoria(parms)
            self.dao.database_commit()

            return id_categoria

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_categoria(self, parm_dict: dict):
        rotina = 'atualizar_categoria'

        try:
            if not parm_dict.get('id_categoria'):
                raise FacadeException(
                    __file__, rotina, 'ID da categoria é obrigatório')

            categoria = self.dao.get_category(
                id_categoria=parm_dict['id_categoria'])
            if not categoria:
                raise FacadeException(
                    __file__, rotina, 'Categoria não encontrada')

            self.dao.update_categoria(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_categoria(self, id_categoria: int):
        rotina = 'apagar_categoria'

        try:
            if not id_categoria:
                raise FacadeException(
                    __file__, rotina, 'ID da categoria é obrigatório')

            categoria = self.dao.get_category(id_categoria=id_categoria)
            if not categoria:
                raise FacadeException(
                    __file__, rotina, 'Categoria não encontrada')

            self.dao.delete_categoria(id_categoria)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
