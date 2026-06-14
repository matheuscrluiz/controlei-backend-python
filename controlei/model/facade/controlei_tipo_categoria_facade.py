from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_tipo_categoria_dao import ControleiTipoCategoriaDAO


class ControleiTipoCategoriaFacade():

    def __init__(self):
        """construtor da classe ControleiTipoCategoriaFacade"""
        self.dao = ControleiTipoCategoriaDAO()

    def obter_tipo_categoria(self, id_tipo_categoria=None) -> dict:
        rotina = 'obter_tipo_categoria'

        try:
            tipo = self.dao.get_type_category(
                id_tipo_categoria=id_tipo_categoria)
            return convert_unique_dic_to_arrayDict(tipo)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_tipo_categoria(self, parm_dict: dict):
        rotina = 'criar_tipo_categoria'

        try:
            dsc = (parm_dict.get('dsc_tipo_categoria') or '').strip()
            if not dsc:
                raise FacadeException(
                    __file__, rotina, 'Descrição do tipo é obrigatória')

            # Dedup pela descrição (não há mais código).
            tipos = self.dao.get_type_category()
            if tipos:
                for tipo in tipos:
                    if (tipo['dsc_tipo_categoria'] or '').strip().upper() \
                            == dsc.upper():
                        raise FacadeException(
                            __file__, rotina,
                            'Tipo de categoria já existente!')

            id_tipo_categoria = self.dao.insert_type_category(
                {'dsc_tipo_categoria': dsc})
            self.dao.database_commit()

            return id_tipo_categoria

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_tipo_categoria(self, parm_dict: dict):
        rotina = 'atualizar_tipo_categoria'

        try:
            if not parm_dict.get('id_tipo_categoria'):
                raise FacadeException(
                    __file__, rotina, 'ID do tipo da categoria é obrigatório')

            tipo = self.dao.get_type_category(
                id_tipo_categoria=parm_dict['id_tipo_categoria'])
            if not tipo:
                raise FacadeException(
                    __file__, rotina, 'Tipo da categoria não encontrado')

            self.dao.update_type_category(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
