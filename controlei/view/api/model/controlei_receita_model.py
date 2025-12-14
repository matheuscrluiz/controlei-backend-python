from flask_restx import Model, fields, Namespace


def generate_receita_model(api: Namespace, type: str) -> Model:
    model = {
        'id_categoria': fields.Integer(
            required=True,
            description="ID da categoria"
        ),
        'id_usuario': fields.Integer(
            required=True,
            description="ID do usuário"
        ),
        'dsc_receita': fields.String(
            required=False,
            description="Descrição da receita"
        ),
        'valor': fields.Float(
            required=True,
            description="Valor da receita"
        ),
        'data_recebimento': fields.Date(
            required=True,
            description="Data de recebimento da receita"
        ),
        'receita_recorrente': fields.String(
            required=False,
            description="Indica se a receita é recorrente (S/N)"
        ),
        'origem_receita': fields.String(
            required=False,
            description="Origem da receita"
        ),
    }

    if type == 'post':
        return api.model(name='post_receita_model', model=model)

    model.update({
        'id_receita': fields.Integer(
            required=True,
            description="ID da receita"
        ),
    })

    return api.model(name='put_receita_model', model=model)
