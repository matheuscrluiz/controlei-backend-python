from flask_restx import fields


def generate_transferencia_model(api, acao):
    """
    Models por ação:
      - entre_contas : id_conta_origem + id_conta_destino + valor.
      - pagar_fatura : id_fatura +
      id_conta_origem (valor é calculado no servidor).
    """
    if acao == 'entre_contas':
        return api.model('TransferenciaEntreContas', {
            'id_conta_origem': fields.Integer(
                required=True, description='Conta de origem'),
            'id_conta_destino': fields.Integer(
                required=True, description='Conta de destino'),
            'valor': fields.Float(required=True,
                                  description='Valor a transferir'),
            'data': fields.String(required=False,
                                  description='Data (YYYY-MM-DD)'),
            'descricao': fields.String(required=False,
                                       description='Descrição'),
        })

    if acao == 'pagar_fatura':
        return api.model('TransferenciaPagarFatura', {
            'id_fatura': fields.Integer(
                required=True, description='Fatura a pagar'),
            'id_conta_origem': fields.Integer(
                required=True, description='Conta de onde sai o dinheiro'),
            'data': fields.String(required=False,
                                  description='Data (YYYY-MM-DD)'),
            'descricao': fields.String(required=False,
                                       description='Descrição'),
        })

    return api.model(f'Transferencia_{acao}', {})
