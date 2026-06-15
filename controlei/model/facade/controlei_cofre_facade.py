from datetime import date, datetime
from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_cofre_dao import ControleiCofreDAO
from ..dao.controlei_transferencia_dao import ControleiTransferenciaDAO
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO


def _normalizar_data(valor):
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), '%Y-%m-%d').date()


def _valor_do_cofre(cofre: dict):
    """Valor de mercado informado; na falta, o aportado líquido."""
    if cofre.get('valor_atual_inform') is not None:
        return cofre['valor_atual_inform']
    return cofre.get('aportado') or 0


class ControleiCofreFacade():

    def __init__(self):
        self.dao = ControleiCofreDAO()
        self.transf_dao = ControleiTransferenciaDAO()
        self.lancamento_dao = ControleiLancamentoDAO()

    def obter_cofre(
            self, id_cofre=None, id_conta=None, id_usuario=None) -> dict:
        rotina = 'obter_cofre'

        try:
            cofres = self.dao.get_cofre(
                id_cofre=id_cofre, id_conta=id_conta, id_usuario=id_usuario)
            cofres = convert_unique_dic_to_arrayDict(cofres)

            # Acrescenta o "valor" (mercado informado, senão aportado).
            for cofre in cofres or []:
                cofre['valor'] = _valor_do_cofre(cofre)

            return cofres

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_cofre(self, parm_dict: dict):
        rotina = 'criar_cofre'

        try:
            id_conta = parm_dict.get('id_conta')
            dsc_cofre = (parm_dict.get('dsc_cofre') or '').strip()

            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'ID da conta é obrigatório')
            if not dsc_cofre:
                raise FacadeException(
                    __file__, rotina, 'Descrição do cofre é obrigatória')

            parms = {
                'id_conta': id_conta,
                'dsc_cofre': dsc_cofre,
                'valor_alvo': parm_dict.get('valor_alvo'),
                'valor_atual_inform': parm_dict.get('valor_atual_inform'),
                'data_valor_atual': parm_dict.get('data_valor_atual'),
                'prioridade': parm_dict.get('prioridade'),
            }

            id_cofre = self.dao.insert_cofre(parms)
            self.dao.database_commit()

            return id_cofre

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_cofre(self, parm_dict: dict):
        rotina = 'atualizar_cofre'

        try:
            if not parm_dict.get('id_cofre'):
                raise FacadeException(
                    __file__, rotina, 'ID do cofre é obrigatório')

            cofre = self.dao.get_cofre(id_cofre=parm_dict['id_cofre'])
            if not cofre:
                raise FacadeException(
                    __file__, rotina, 'Cofre não encontrado')

            self.dao.update_cofre(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def informar_valor_atual(self, parm_dict: dict):
        """Atualiza o valor de mercado do cofre 
        (nível 'médio' do investimento)."""
        rotina = 'informar_valor_atual'

        try:
            if not parm_dict.get('id_cofre'):
                raise FacadeException(
                    __file__, rotina, 'ID do cofre é obrigatório')

            parms = {
                'id_cofre': parm_dict['id_cofre'],
                'valor_atual_inform': parm_dict.get('valor_atual_inform'),
                'data_valor_atual': _normalizar_data(
                    parm_dict.get('data_valor_atual')),
            }

            self.dao.update_valor_atual(parms)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_cofre(self, id_cofre: int):
        rotina = 'deletar_cofre'

        try:
            if not id_cofre:
                raise FacadeException(
                    __file__, rotina, 'ID do cofre é obrigatório')

            cofre = self.dao.get_cofre(id_cofre=id_cofre)
            if not cofre:
                raise FacadeException(
                    __file__, rotina, 'Cofre não encontrado')

            # Não deixa apagar cofre com dinheiro dentro — resgate antes.
            if Decimal(str(cofre[0].get('aportado') or 0)) != 0:
                raise FacadeException(
                    __file__, rotina,
                    'Resgate todo o valor antes de apagar o cofre')

            self.dao.delete_cofre(id_cofre)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def aportar(self, parm_dict: dict):
        """saldo da conta -> cofre. Baixa o saldo e registra o aporte."""
        rotina = 'aportar'

        try:
            id_cofre = parm_dict.get('id_cofre')
            valor = parm_dict.get('valor')
            data = _normalizar_data(parm_dict.get('data'))

            if not id_cofre:
                raise FacadeException(
                    __file__, rotina, 'ID do cofre é obrigatório')
            if not valor or Decimal(str(valor)) <= 0:
                raise FacadeException(
                    __file__, rotina, 'Valor deve ser maior que zero')

            cofre = self.dao.get_cofre(id_cofre=id_cofre)
            if not cofre:
                raise FacadeException(
                    __file__, rotina, 'Cofre não encontrado')
            id_conta = cofre[0]['id_conta']
            valor = abs(Decimal(str(valor)))
            descricao = parm_dict.get('descricao') \
                or ('Aporte: %s' % cofre[0].get('dsc_cofre'))

            self._movimentar(
                'aporte', id_cofre, id_conta, valor, data, descricao)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def resgatar(self, parm_dict: dict):
        """cofre -> saldo da conta. Repõe o saldo e registra o resgate."""
        rotina = 'resgatar'

        try:
            id_cofre = parm_dict.get('id_cofre')
            valor = parm_dict.get('valor')
            data = _normalizar_data(parm_dict.get('data'))

            if not id_cofre:
                raise FacadeException(
                    __file__, rotina, 'ID do cofre é obrigatório')
            if not valor or Decimal(str(valor)) <= 0:
                raise FacadeException(
                    __file__, rotina, 'Valor deve ser maior que zero')

            cofre = self.dao.get_cofre(id_cofre=id_cofre)
            if not cofre:
                raise FacadeException(
                    __file__, rotina, 'Cofre não encontrado')
            id_conta = cofre[0]['id_conta']
            valor = abs(Decimal(str(valor)))
            descricao = parm_dict.get('descricao') \
                or ('Resgate: %s' % cofre[0].get('dsc_cofre'))

            self._movimentar(
                'resgate', id_cofre, id_conta, valor, data, descricao)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def _movimentar(self, tipo, id_cofre, id_conta, valor, data, descricao):
        """
        Engrenagem comum de aporte/resgate:
          1) transferência (metadado)  2) lançamento (move o saldo)
          3) cofre_movimentacao (registra no cofre)
        Aporte baixa o saldo (-); resgate repõe (+).
        """
        if tipo == 'aporte':
            sinal_saldo = -valor
            origem, destino = id_conta, None
        else:  # resgate
            sinal_saldo = valor
            origem, destino = None, id_conta

        id_transf = self.transf_dao.insert_transferencia({
            'tipo': tipo,
            'valor': valor,
            'data': data,
            'descricao': descricao,
            'id_conta_origem': origem,
            'id_conta_destino': destino,
            'id_cofre': id_cofre,
        })
        self.transf_dao.database_commit()

        id_lanc = self.lancamento_dao.insert_lancamento({
            'id_conta': id_conta, 'natureza': 'transferencia',
            'valor': sinal_saldo, 'data': data, 'descricao': descricao,
            'id_transferencia': id_transf, 'status': 'efetivado',
        })
        self.lancamento_dao.database_commit()

        self.dao.insert_movimentacao({
            'id_cofre': id_cofre, 'id_lancamento': id_lanc,
            'tipo': tipo, 'valor': valor, 'data': data,
        })
        self.dao.database_commit()

        return id_transf
