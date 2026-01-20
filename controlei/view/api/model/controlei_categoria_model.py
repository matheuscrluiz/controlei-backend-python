from flask_restx import Model, fields, Namespace


def generate_categoria_model(api: Namespace, type: str) -> Model:
    model = {
        'dsc_categoria': fields.String(
            required=True,
            description="Dsc. do categoria"
        ),
        'id_tipo_categoria': fields.Integer(
            required=True,
            description="ID do tipo de categoria"
        ),

    }

    if type == 'post':
        return api.model(name='post_categoria_model', model=model)

    model.update({
        'id_categoria': fields.Integer(
            required=True,
            description="ID do categoria"
        ),

    })
    return api.model(name='put_categoria_model', model=model)
