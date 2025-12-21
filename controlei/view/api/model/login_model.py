from flask_restx import Model, fields, Namespace


def generate_login_model(api: Namespace) -> Model:
    """Modelo para requisição de login"""
    model = api.model('Login', {
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),
        'senha': fields.String(
            required=True,
            description="Senha do usuário"
        )
    })
    return model


def generate_login_response_model(api: Namespace) -> Model:
    """Modelo para resposta de login bem-sucedida"""
    model = api.model('LoginResponse', {
        'id_usuario': fields.Integer(
            description="ID do usuário"
        ),
        'ch_rede': fields.String(
            description="Chave de rede do usuário"
        ),
        'nome': fields.String(
            description="Nome do usuário"
        ),
        'email': fields.String(
            description="E-mail do usuário"
        ),
        'matricula': fields.String(
            description="Matrícula do usuário"
        )
    })
    return model
