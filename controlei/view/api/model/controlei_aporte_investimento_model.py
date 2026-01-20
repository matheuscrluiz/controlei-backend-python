from flask_restx import Model, fields, Namespace


def generate_aporte_investimento_model(api: Namespace, type: str) -> Model:
    model = {
        'id_investimento': fields.Integer(
            required=True,
            description="ID do investimento"
        ),
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),

        'valor_aporte': fields.Float(
            required=True,
            description="Valor do aporte"
        ),
        'data_aporte': fields.Date(
            required=True,
            description="Data de aporte da investimento"
        ),

    }

    if type == 'post':
        return api.model(name='post_aporte_investimento_model', model=model)

    model.update({
        'id_aporte': fields.Integer(
            required=True,
            description="ID do aporte"
        ),
    })

    return api.model(name='put_aporte_investimento_model', model=model)
