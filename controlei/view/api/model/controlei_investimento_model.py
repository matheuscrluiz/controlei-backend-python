from flask_restx import Model, fields, Namespace


def generate_investimento_model(api: Namespace, type: str) -> Model:
    model = {
        'id_categoria': fields.Integer(
            required=True,
            description="ID da categoria"
        ),
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),
        'nome_investimento': fields.String(
            required=False,
            description="nome do investimento"
        ),
        'valor_inicial': fields.Float(
            required=True,
            description="Valor da investimento"
        ),
        'data_inicio': fields.Date(
            required=True,
            description="Data de incio da investimento"
        ),
        'data_fim': fields.Date(
            description="Data de fim da investimento"
        ),
        'id_instituicao': fields.Integer(
            required=False,
            description="ID da instituição"
        ),
    }

    if type == 'post':
        return api.model(name='post_investimento_model', model=model)

    model.update({
        'id_investimento': fields.Integer(
            required=True,
            description="ID do investimento"
        ),
    })

    return api.model(name='put_investimento_model', model=model)
