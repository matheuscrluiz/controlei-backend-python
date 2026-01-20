from flask_restx import Model, fields, Namespace


def generate_meta_movimentacao_model(api: Namespace, type: str) -> Model:
    model = {
        'id_meta': fields.Integer(
            required=True,
            description="ID da meta"
        ),
        'valor': fields.Float(
            required=True,
            description="Valor da movimentação"
        ),
        'data_movimentacao': fields.Date(
            required=True,
            description="Data da movimentação"
        ),
        'origem': fields.String(
            # required=True,
            description="Origem da movimentação"
        ),
    }

    if type == 'post':
        return api.model(name='post_meta_movimentacao_model', model=model)

    model.update({
        'id_movimentacao': fields.Integer(
            required=True,
            description="ID da movimentação"
        ),
    })

    return api.model(name='put_meta_movimentacao_model', model=model)
