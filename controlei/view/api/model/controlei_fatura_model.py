from flask_restx import fields


def generate_fatura_model(api, method):
    """
    Model Flask-RESTX da fatura.
      - post: id_cartao + competencia (obter-ou-criar a fatura do mês).
      - put : id_fatura + status (aberta | fechada | paga).
    """
    if method == 'post':
        return api.model('Fatura_post', {
            'id_cartao': fields.Integer(
                required=True, description='ID do cartão'),
            'competencia': fields.String(
                required=True,
                description='Mês de referência (YYYY-MM ou YYYY-MM-DD)'),
        })

    if method == 'put':
        return api.model('Fatura_put', {
            'id_fatura': fields.Integer(
                required=True, description='ID da fatura'),
            'status': fields.String(
                required=True, description='aberta | fechada | paga'),
        })

    return api.model(f'Fatura_{method}', {})
