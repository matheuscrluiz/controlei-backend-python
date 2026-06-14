from flask_restx import fields


def generate_cartao_model(api, method):
    """
    Model Flask-RESTX do cartão.
      - post: id_conta + apelido + funcao obrigatórios; resto opcional.
      - put : id_cartao + apelido + funcao obrigatórios; resto opcional.
    funcao: credito | debito | multiplo
    Obs.: dia_fechamento/dia_vencimento são exigidos pelo facade quando a
    função envolve crédito.
    """
    campos = {
        'apelido': fields.String(
            required=True, description='Apelido do cartão'),
        'funcao': fields.String(
            required=True, description='credito | debito | multiplo'),
        'bandeira': fields.String(
            required=False, description='Visa, Master, Elo...'),
        'ultimos4': fields.String(
            required=False, description='Últimos 4 dígitos'),
        'limite': fields.Float(
            required=False, description='Limite (crédito)'),
        'dia_fechamento': fields.Integer(
            required=False, description='Dia de fechamento (crédito)'),
        'dia_vencimento': fields.Integer(
            required=False, description='Dia de vencimento (crédito)'),
        'id_cartao_pai': fields.Integer(
            required=False, description='Cartão pai (cartão virtual)'),
    }

    if method == 'post':
        campos['id_conta'] = fields.Integer(
            required=True, description='ID da conta dona do cartão')

    if method == 'put':
        campos['id_cartao'] = fields.Integer(
            required=True, description='ID do cartão')

    return api.model(f'Cartao_{method}', campos)
