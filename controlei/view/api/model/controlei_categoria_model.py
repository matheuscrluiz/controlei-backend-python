from flask_restx import fields


def generate_categoria_model(api, method):
    """
    Model Flask-RESTX da categoria.
      - post: id_usuario + dsc_categoria + id_tipo_categoria obrigatórios.
      - put : id_categoria + dsc_categoria + id_tipo_categoria obrigatórios.
    """
    campos = {
        'dsc_categoria': fields.String(
            required=True, description='Descrição da categoria'),
        'id_tipo_categoria': fields.Integer(
            required=True, description='Tipo da categoria (receita/despesa)'),
    }

    if method == 'post':
        campos['id_usuario'] = fields.Integer(
            required=True, description='ID do usuário dono da categoria')

    if method == 'put':
        campos['id_categoria'] = fields.Integer(
            required=True, description='ID da categoria')

    return api.model(f'Categoria_{method}', campos)
