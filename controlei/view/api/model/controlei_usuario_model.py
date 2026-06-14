from flask_restx import fields


def generate_usuario_model(api, method):
    """
    Gera o model Flask-RESTX do usuário conforme o método.
      - post: nome, email, senha (todos obrigatórios)
      - put : id_usuario + nome + email obrigatórios; senha opcional (troca)
    """
    campos = {
        'nome': fields.String(required=True, description='Nome do usuário'),
        'email': fields.String(required=True, description='E-mail do usuário'),
    }

    if method == 'post':
        campos['senha'] = fields.String(
            required=True, description='Senha do usuário')

    if method == 'put':
        campos['id_usuario'] = fields.Integer(
            required=True, description='ID do usuário')
        campos['senha'] = fields.String(
            required=False, description='Nova senha (opcional)')

    return api.model(f'Usuario_{method}', campos)
