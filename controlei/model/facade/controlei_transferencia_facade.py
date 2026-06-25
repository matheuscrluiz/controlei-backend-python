from datetime import date, datetime
from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_transferencia_dao import ControleiTransferenciaDAO
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO
from .controlei_fatura_facade import ControleiFaturaFacade


def _normalizar_data(valor):
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), '%Y-%m-%d').date()


class ControleiTransferenciaFacade():
    """
    Mecanismo genérico que move dinheiro. Cada perna do SALDO é um lançamento
    natureza='transferencia' (que NÃO conta como receita/despesa). A tabela
    transferencia guarda o metadado e as pontas.

    Obs. de atomicidade: como cada DAO tem sua conexão, a transferência é
    confirmada antes das pernas (a FK exige a transferência commitada). No raro
    caso de falha entre os passos, pode sobrar uma transferência sem pernas —
    inofensiva. Atomicidade total exigiria conexão/transação compartilhada.
    """

    def __init__(self):
        self.dao = ControleiTransferenciaDAO()
        self.lancamento_dao = ControleiLancamentoDAO()
        self.fatura_facade = ControleiFaturaFacade()

    def obter_transferencia(self, **filtros) -> dict:
        rotina = 'obter_transferencia'

        try:
            transfs = self.dao.get_transferencia(**filtros)
            return convert_unique_dic_to_arrayDict(transfs)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def transferir_entre_contas(self, parm_dict: dict):
        """Move dinheiro do saldo da conta origem para o da conta destino."""
        rotina = 'transferir_entre_contas'

        try:
            id_origem = parm_dict.get('id_conta_origem')
            id_destino = parm_dict.get('id_conta_destino')
            valor = parm_dict.get('valor')
            data = _normalizar_data(parm_dict.get('data'))
            descricao = parm_dict.get(
                'descricao') or 'Transferência entre contas'

            if not id_origem or not id_destino:
                raise FacadeException(
                    __file__, rotina,
                    'Conta de origem e destino são obrigatórias')
            if int(id_origem) == int(id_destino):
                raise FacadeException(
                    __file__, rotina,
                    'Origem e destino não podem ser a mesma conta')
            if not valor or Decimal(str(valor)) <= 0:
                raise FacadeException(
                    __file__, rotina, 'Valor deve ser maior que zero')

            valor = abs(Decimal(str(valor)))

            # 1) Transferência (commitada — a FK das pernas precisa dela).
            id_transf = self.dao.insert_transferencia({
                'tipo': 'entre_contas',
                'valor': valor,
                'data': data,
                'descricao': descricao,
                'id_conta_origem': id_origem,
                'id_conta_destino': id_destino,
            })
            self.dao.database_commit()

            # 2) Duas pernas: saída na origem, entrada no destino.
            self.lancamento_dao.insert_lancamento({
                'id_conta': id_origem, 'natureza': 'transferencia',
                'valor': -valor, 'data': data, 'descricao': descricao,
                'id_transferencia': id_transf, 'status': 'efetivado',
            })
            self.lancamento_dao.insert_lancamento({
                'id_conta': id_destino, 'natureza': 'transferencia',
                'valor': valor, 'data': data, 'descricao': descricao,
                'id_transferencia': id_transf, 'status': 'efetivado',
            })
            self.lancamento_dao.database_commit()

            return id_transf

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def pagar_fatura(self, parm_dict: dict):
        """
        Paga a fatura por completo: baixa o saldo da conta de origem (pode ser
        qualquer conta) e marca a fatura como paga (as parcelas viram pagas por
        reflexo). Pagamento total — o valor é o total calculado no servidor.
        """
        rotina = 'pagar_fatura'

        try:
            id_fatura = parm_dict.get('id_fatura')
            id_origem = parm_dict.get('id_conta_origem')
            data = _normalizar_data(parm_dict.get('data'))

            if not id_fatura:
                raise FacadeException(
                    __file__, rotina, 'ID da fatura é obrigatório')
            if not id_origem:
                raise FacadeException(
                    __file__, rotina, 'Conta de origem é obrigatória')

            fatura = self.fatura_facade.obter_fatura(id_fatura=id_fatura)
            if not fatura:
                raise FacadeException(
                    __file__, rotina, 'Fatura não encontrada')
            if (fatura[0].get('status') or '').lower() == 'paga':
                raise FacadeException(
                    __file__, rotina, 'Fatura já está paga')

            total = Decimal(
                str(self.fatura_facade.obter_total_fatura(id_fatura)))
            descricao = parm_dict.get('descricao') or 'Pagamento de fatura'

            # 1) Transferência (commitada antes da perna).
            id_transf = self.dao.insert_transferencia({
                'tipo': 'pagamento_fatura',
                'valor': total,
                'data': data,
                'descricao': descricao,
                'id_conta_origem': id_origem,
                'id_fatura': id_fatura,
            })
            self.dao.database_commit()

            # 2) Perna do saldo: saída da conta origem (só se há o que pagar).
            if total > 0:
                self.lancamento_dao.insert_lancamento({
                    'id_conta': id_origem, 'natureza': 'transferencia',
                    'valor': -total, 'data': data, 'descricao': descricao,
                    'id_transferencia': id_transf, 'status': 'efetivado',
                })
                self.lancamento_dao.database_commit()

            # 3) Fatura paga (parcelas viram pagas por reflexo do status).
            self.fatura_facade.atualizar_status_fatura(id_fatura, 'paga')

            return id_transf

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
