from flask_restx import fields


def generate_login_model(api):
    """Payload de login: e-mail + senha."""
    return api.model('Login', {
        'email': fields.String(
            required=True, description='E-mail do usuário'),
        'senha': fields.String(
            required=True, description='Senha do usuário'),
    })


def generate_login_response_model(api):
    """Resposta do login: dados do usuário autenticado (sem hash)."""
    return api.model('LoginResponse', {
        'id_usuario': fields.Integer(description='ID do usuário'),
        'nome': fields.String(description='Nome do usuário'),
        'email': fields.String(description='E-mail do usuário'),
        'onboarded': fields.Boolean(
            description='Usuário já tem conta (passou pelo onboarding)'),
    })
