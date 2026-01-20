from flask_restx import Model, fields, Namespace


def generate_meta_model(api: Namespace, type: str) -> Model:
    model = {
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),
        'dsc_meta': fields.String(
            required=False,
            description="Descrição da meta"
        ),
        'valor_meta': fields.Float(
            required=True,
            description="Valor da meta"
        ),
        'prioridade': fields.Integer(
            required=False,
            description="Prioridade da meta"
        ),
        'ativa': fields.String(
            # required=False,
            description="Se meta está ativa"
        ),
    }

    if type == 'post':
        return api.model(name='post_meta_model', model=model)

    model.update({
        'id_meta': fields.Integer(
            required=True,
            description="ID da meta"
        ),
    })

    return api.model(name='put_meta_model', model=model)
