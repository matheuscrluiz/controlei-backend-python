from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_fatura_item_dao import ControleiFaturaItemDAO

TIPOS_VALIDOS = ('abertura', 'encargo', 'estorno', 'credito')
# Encargo e abertura SOMAM na fatura; estorno e crédito ABATEM.
TIPOS_NEGATIVOS = ('estorno', 'credito')


class ControleiFaturaItemFacade():

    def __init__(self):
        """construtor da classe ControleiFaturaItemFacade"""
        self.dao = ControleiFaturaItemDAO()

    def obter_fatura_item(self, id_fatura_item=None, id_fatura=None,
                          id_compra=None, tipo=None) -> dict:
        rotina = 'obter_fatura_item'

        try:
            itens = self.dao.get_fatura_item(
                id_fatura_item=id_fatura_item,
                id_fatura=id_fatura,
                id_compra=id_compra,
                tipo=tipo)
            return convert_unique_dic_to_arrayDict(itens)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_fatura_item(self, parm_dict: dict):
        """
        Cria uma linha avulsa na fatura. O sinal é normalizado pelo tipo:
        encargo/abertura entram positivos; estorno/credito entram negativos.
        A API manda sempre o valor positivo + o tipo.
        """
        rotina = 'criar_fatura_item'

        try:
            id_fatura = parm_dict.get('id_fatura')
            tipo = (parm_dict.get('tipo') or '').strip().lower()
            valor = parm_dict.get('valor')

            if not id_fatura:
                raise FacadeException(
                    __file__, rotina, 'ID da fatura é obrigatório')
            if tipo not in TIPOS_VALIDOS:
                raise FacadeException(
                    __file__, rotina,
                    'Tipo inválido (abertura, encargo, estorno ou credito)')
            if valor is None or Decimal(str(valor)) == 0:
                raise FacadeException(
                    __file__, rotina,
                    'Valor é obrigatório e diferente de zero')

            v = abs(Decimal(str(valor)))
            if tipo in TIPOS_NEGATIVOS:
                v = -v

            id_item = self.dao.insert_fatura_item({
                'id_fatura': id_fatura,
                'id_compra': parm_dict.get('id_compra'),
                'tipo': tipo,
                'descricao': parm_dict.get('descricao'),
                'valor': v,
                'import_ref': parm_dict.get('import_ref'),
            })
            self.dao.database_commit()

            return id_item

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_fatura_item(self, id_fatura_item: int):
        rotina = 'apagar_fatura_item'

        try:
            if not id_fatura_item:
                raise FacadeException(
                    __file__, rotina, 'ID do item é obrigatório')

            item = self.dao.get_fatura_item(id_fatura_item=id_fatura_item)
            if not item:
                raise FacadeException(
                    __file__, rotina, 'Item de fatura não encontrado')

            self.dao.delete_fatura_item(id_fatura_item)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
