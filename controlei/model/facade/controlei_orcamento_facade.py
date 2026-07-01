from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_orcamento_dao import ControleiOrcamentoDAO


class ControleiOrcamentoFacade():

    def __init__(self):
        self.dao = ControleiOrcamentoDAO()

    def obter_orcamento(
            self,
            id_orcamento=None,
            id_usuario=None,
            id_categoria=None) -> dict:
        rotina = 'obter_orcamento'

        try:
            orcamento = self.dao.get_orcamento(
                id_orcamento=id_orcamento,
                id_usuario=id_usuario,
                id_categoria=id_categoria)
            return convert_unique_dic_to_arrayDict(orcamento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_orcamento(self, parm_dict: dict):
        rotina = 'criar_orcamento'

        try:
            id_usuario = parm_dict.get('id_usuario')
            id_categoria = parm_dict.get('id_categoria')
            valor_teto = parm_dict.get('valor_teto')

            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')
            if not id_categoria:
                raise FacadeException(
                    __file__, rotina, 'Categoria é obrigatória')
            if valor_teto is None or float(valor_teto) <= 0:
                raise FacadeException(
                    __file__, rotina, 'O teto deve ser maior que zero')

            existente = self.dao.get_orcamento(
                id_usuario=id_usuario, id_categoria=id_categoria)
            if existente:
                raise FacadeException(
                    __file__, rotina,
                    'Já existe um orçamento para esta categoria')

            id_orcamento = self.dao.insert_orcamento({
                'id_usuario': id_usuario,
                'id_categoria': id_categoria,
                'valor_teto': valor_teto,
            })
            self.dao.database_commit()

            return id_orcamento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_orcamento(self, parm_dict: dict):
        rotina = 'atualizar_orcamento'

        try:
            if not parm_dict.get('id_orcamento'):
                raise FacadeException(
                    __file__, rotina, 'ID do orçamento é obrigatório')

            valor_teto = parm_dict.get('valor_teto')
            if valor_teto is None or float(valor_teto) <= 0:
                raise FacadeException(
                    __file__, rotina, 'O teto deve ser maior que zero')

            orcamento = self.dao.get_orcamento(
                id_orcamento=parm_dict['id_orcamento'])
            if not orcamento:
                raise FacadeException(
                    __file__, rotina, 'Orçamento não encontrado')

            self.dao.update_orcamento(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_orcamento(self, id_orcamento: int):
        rotina = 'apagar_orcamento'

        try:
            if not id_orcamento:
                raise FacadeException(
                    __file__, rotina, 'ID do orçamento é obrigatório')

            orcamento = self.dao.get_orcamento(id_orcamento=id_orcamento)
            if not orcamento:
                raise FacadeException(
                    __file__, rotina, 'Orçamento não encontrado')

            self.dao.delete_orcamento(id_orcamento)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
