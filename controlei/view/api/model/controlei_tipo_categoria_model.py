from flask_restx import Model, fields, Namespace


def generate_tipo_categoria_model(api: Namespace, type: str) -> Model:
    model = {
        'dsc_tipo_categoria': fields.String(
            required=True,
            description="Dsc. do tipo de categoria"
        ),
        'codigo_tipo_categoria': fields.String(
            required=True,
            description="Código do tipo da categoria"
        ),

    }

    if type == 'post':
        return api.model(name='post_tipo_categoria_model', model=model)

    model.update({
        'id_tipo_categoria': fields.Integer(
            required=True,
            description="ID do tipo de categoria"
        ),

    })
    return api.model(name='put_tipo_categoria_model', model=model)
