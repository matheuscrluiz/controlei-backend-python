from flask_restx import Model, fields, Namespace


def generate_usuario_model(api: Namespace, type: str) -> Model:
    model = {
        'nome': fields.String(
            required=True,
            description="Nome do usuário"
        ),
        'senha': fields.String(
            required=True,
            description="Senha do usuário"
        ),
        'email': fields.String(
            required=True,
            description="E-mail do usuário"
        )
    }

    if type == 'post':
        return api.model(name='post_usuario_model', model=model)

    model.update({
        'id_usuario': fields.Integer(
            required=True,
            description="ID do usuário"
        ),
        'alterado_em': fields.Date(
            required=True,
            description="Data da alteração"
        ),

    })
    return api.model(name='put_usuario_model', model=model)
