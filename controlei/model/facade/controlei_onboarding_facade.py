from decimal import Decimal
from ...util.exceptions import FacadeException
from ..dao.controlei_conta_dao import ControleiContaDAO
from .controlei_lancamento_facade import ControleiLancamentoFacade
from .controlei_cartao_facade import ControleiCartaoFacade


class ControleiOnboardingFacade():
    """
    Orquestra a primeira configuração do usuário numa chamada só:
      1) cria a conta;
      2) se houver saldo de abertura, lança um ajuste (natureza='ajuste');
      3) opcionalmente cria o primeiro cartão.
    """

    def __init__(self):
        self.conta_dao = ControleiContaDAO()
        self.lancamento_facade = ControleiLancamentoFacade()
        self.cartao_facade = ControleiCartaoFacade()

    def realizar_onboarding(self, parm_dict: dict):
        rotina = 'realizar_onboarding'

        try:
            id_usuario = parm_dict.get('id_usuario')
            apelido = (parm_dict.get('apelido') or '').strip()

            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')
            if not apelido:
                raise FacadeException(
                    __file__, rotina, 'Apelido da conta é obrigatório')

            # 1) Conta
            id_conta = self.conta_dao.insert_conta({
                'id_usuario': id_usuario,
                'id_instituicao': parm_dict.get('id_instituicao'),
                'apelido': apelido,
                'tipo': parm_dict.get('tipo') or 'corrente',
            })
            self.conta_dao.database_commit()

            # 2) Saldo de abertura (só se diferente de zero)
            id_lancamento = None
            saldo = parm_dict.get('saldo_abertura')
            if saldo is not None and Decimal(str(saldo)) != 0:
                id_lancamento = self.lancamento_facade.criar_lancamento({
                    'id_conta': id_conta,
                    'natureza': 'ajuste',
                    'valor': saldo,
                    'descricao': 'Saldo de abertura',
                    'status': 'efetivado',
                })

            # 3) Primeiro cartão (opcional)
            id_cartao = None
            cartao = parm_dict.get('cartao')
            if cartao and (cartao.get('apelido') or '').strip():
                dados_cartao = dict(cartao)
                dados_cartao['id_conta'] = id_conta
                id_cartao = self.cartao_facade.criar_cartao(dados_cartao)

            return {
                'id_conta': id_conta,
                'id_lancamento': id_lancamento,
                'id_cartao': id_cartao,
            }

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
