from flask_restx import fields


def generate_orcamento_model(api, method):
    """
    Model Flask-RESTX do orçamento.
      - post: id_usuario + id_categoria + valor_teto obrigatórios.
      - put : id_orcamento + valor_teto obrigatórios.
    """
    campos = {
        'valor_teto': fields.Float(
            required=True, description='Teto mensal da categoria'),
    }

    if method == 'post':
        campos['id_usuario'] = fields.Integer(
            required=True, description='ID do usuário')
        campos['id_categoria'] = fields.Integer(
            required=True, description='ID da categoria')

    if method == 'put':
        campos['id_orcamento'] = fields.Integer(
            required=True, description='ID do orçamento')

    return api.model(f'Orcamento_{method}', campos)
