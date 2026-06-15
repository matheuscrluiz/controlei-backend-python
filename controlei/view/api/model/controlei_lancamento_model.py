from flask_restx import fields


def generate_lancamento_model(api, method):
    """
    Model Flask-RESTX do lançamento.
      - post: id_conta + natureza + valor obrigatórios; resto opcional.
      - put : id_lancamento obrigatório; campos editáveis opcionais.
    natureza: receita | despesa | transferencia | ajuste
    Valor é POSITIVO; o sinal é aplicado pela natureza no facade.
    """
    if method == 'post':
        return api.model('Lancamento_post', {
            'id_conta': fields.Integer(
                required=True, description='ID da conta'),
            'natureza': fields.String(
                required=True,
                description='receita | despesa | transferencia | ajuste'),
            'valor': fields.Float(
                required=True, description='Valor positivo'),
            'data': fields.String(
                required=False, description='Data (YYYY-MM-DD)'),
            'descricao': fields.String(
                required=False, description='Descrição'),
            'id_categoria': fields.Integer(
                required=False, description='ID da categoria'),
            'id_cartao': fields.Integer(
                required=False,
                description='Cartão de débito usado (etiqueta)'),
            'status': fields.String(
                required=False, description='efetivado | previsto'),
        })

    if method == 'put':
        return api.model('Lancamento_put', {
            'id_lancamento': fields.Integer(
                required=True, description='ID do lançamento'),
            'natureza': fields.String(
                required=False, description='receita | despesa | ...'),
            'valor': fields.Float(required=False,
                                  description='Valor positivo'),
            'data': fields.String(required=False,
                                  description='Data (YYYY-MM-DD)'),
            'descricao': fields.String(required=False,
                                       description='Descrição'),
            'id_categoria': fields.Integer(
                required=False, description='ID da categoria'),
            'id_cartao': fields.Integer(
                required=False, description='Cartão de débito (etiqueta)'),
        })

    return api.model(f'Lancamento_{method}', {})
