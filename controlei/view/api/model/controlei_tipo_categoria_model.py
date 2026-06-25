from flask_restx import fields


def generate_tipo_categoria_model(api, method):
    """
    Model Flask-RESTX do tipo de categoria.
      - post: dsc_tipo_categoria obrigatório.
      - put : id_tipo_categoria + dsc_tipo_categoria obrigatórios.
    """
    campos = {
        'dsc_tipo_categoria': fields.String(
            required=True, description='Descrição do tipo (ex.: receita)'),
    }

    if method == 'put':
        campos['id_tipo_categoria'] = fields.Integer(
            required=True, description='ID do tipo da categoria')

    return api.model(f'TipoCategoria_{method}', campos)
