from flask_restx import Model, fields, Namespace


def generate_rendimento_investimento_model(api: Namespace, type: str) -> Model:
    model = {
        'id_investimento': fields.Integer(
            required=True,
            description="ID do investimento"
        ),
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),

        'valor_rendimento': fields.Float(
            required=True,
            description="Valor do rendimento"
        ),
        'mes_referencia': fields.Date(
            required=True,
            description="Data de referencia do rendimento"
        ),

    }

    if type == 'post':
        return api.model(name='post_rendimento_investimento_model',
                         model=model)

    model.update({
        'id_rendimento': fields.Integer(
            required=True,
            description="ID do rendimento"
        ),
    })

    return api.model(name='put_rendimento_investimento_model', model=model)
