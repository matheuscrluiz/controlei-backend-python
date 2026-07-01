from datetime import date, datetime
from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO

NATUREZAS_VALIDAS = ('receita', 'despesa', 'transferencia', 'ajuste')


def _normalizar_data(valor):
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), '%Y-%m-%d').date()


def _aplicar_sinal(natureza: str, valor):
    """
    receita -> +abs ; despesa -> -abs.
    ajuste/transferencia -> usa o sinal como veio (são internos).
    """
    v = Decimal(str(valor))
    if natureza == 'receita':
        return abs(v)
    if natureza == 'despesa':
        return -abs(v)
    return v


class ControleiLancamentoFacade():

    def __init__(self):
        """construtor da classe ControleiLancamentoFacade"""
        self.dao = ControleiLancamentoDAO()

    def obter_lancamento(self, **filtros) -> dict:
        rotina = 'obter_lancamento'

        try:
            lancamentos = self.dao.get_lancamento(**filtros)
            return convert_unique_dic_to_arrayDict(lancamentos)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_lancamento(self, parm_dict: dict):
        rotina = 'criar_lancamento'

        try:
            id_conta = parm_dict.get('id_conta')
            natureza = (parm_dict.get('natureza') or '').strip().lower()
            valor = parm_dict.get('valor')

            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'ID da conta é obrigatório')
            if natureza not in NATUREZAS_VALIDAS:
                raise FacadeException(
                    __file__, rotina,
                    'Natureza inválida (receita, despesa, transferencia, '
                    'ajuste)')
            if valor is None or Decimal(str(valor)) == 0:
                raise FacadeException(
                    __file__, rotina, 'Valor é obrigatório e diferente de zero')

            parms = {
                'id_conta': id_conta,
                'id_categoria': parm_dict.get('id_categoria'),
                'id_cartao': parm_dict.get('id_cartao'),
                'id_transferencia': parm_dict.get('id_transferencia'),
                'id_recorrencia': parm_dict.get('id_recorrencia'),
                'natureza': natureza,
                'valor': _aplicar_sinal(natureza, valor),
                'data': _normalizar_data(parm_dict.get('data')),
                'descricao': parm_dict.get('descricao'),
                'status': (parm_dict.get('status') or 'efetivado'),
                'import_ref': parm_dict.get('import_ref'),
            }

            id_lancamento = self.dao.insert_lancamento(parms)
            self.dao.database_commit()

            return id_lancamento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_lancamento(self, parm_dict: dict):
        rotina = 'atualizar_lancamento'

        try:
            id_lancamento = parm_dict.get('id_lancamento')
            if not id_lancamento:
                raise FacadeException(
                    __file__, rotina, 'ID do lançamento é obrigatório')

            atual = self.dao.get_lancamento(id_lancamento=id_lancamento)
            if not atual:
                raise FacadeException(
                    __file__, rotina, 'Lançamento não encontrado')

            natureza = (parm_dict.get('natureza')
                        or atual[0]['natureza']).strip().lower()
            valor = parm_dict.get('valor')

            parms = {
                'id_lancamento': id_lancamento,
                'id_categoria': parm_dict.get('id_categoria'),
                'id_cartao': parm_dict.get('id_cartao'),
                'natureza': natureza,
                'valor': _aplicar_sinal(natureza, valor) if valor is not None
                else atual[0]['valor'],
                'data': _normalizar_data(parm_dict.get('data')
                                         or atual[0]['data']),
                'descricao': parm_dict.get('descricao'),
            }

            self.dao.update_lancamento(parms)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def confirmar_lancamento(self, id_lancamento: int, valor=None):
        """Confirma um lançamento 'previsto'. Se `valor` vier (recorrência
        variável), atualiza o valor (com sinal pela natureza) antes de efetivar."""
        rotina = 'confirmar_lancamento'

        try:
            if not id_lancamento:
                raise FacadeException(
                    __file__, rotina, 'ID do lançamento é obrigatório')

            if valor is not None:
                atual = self.dao.get_lancamento(id_lancamento=id_lancamento)
                if not atual:
                    raise FacadeException(
                        __file__, rotina, 'Lançamento não encontrado')
                natureza = atual[0]['natureza']
                self.dao.update_valor_lancamento(
                    id_lancamento, _aplicar_sinal(natureza, valor))

            self.dao.update_status_lancamento(id_lancamento, 'efetivado')
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_lancamento(self, id_lancamento: int):
        rotina = 'deletar_lancamento'

        try:
            if not id_lancamento:
                raise FacadeException(
                    __file__, rotina, 'ID do lançamento é obrigatório')

            atual = self.dao.get_lancamento(id_lancamento=id_lancamento)
            if not atual:
                raise FacadeException(
                    __file__, rotina, 'Lançamento não encontrado')

            self.dao.delete_lancamento(id_lancamento)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
