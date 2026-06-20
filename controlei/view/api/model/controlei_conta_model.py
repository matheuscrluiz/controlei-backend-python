from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger, NullableFloat, NullableString)


def generate_conta_model(api, method):
    """
    Model Flask-RESTX da conta.
      - post: id_usuario + apelido obrigatórios; demais opcionais.
              saldo_abertura opcional -> vira lançamento de ajuste.
      - put : id_conta + apelido obrigatórios; id_instituicao/tipo opcionais.
    tipo: corrente | poupanca | carteira | corretora | outra
    """
    campos = {
        'apelido': fields.String(
            required=True, description='Apelido da conta'),
        'id_instituicao': NullableInteger(
            required=False, description='ID da instituição'),
        'tipo': NullableString(
            required=False,
            description='corrente | poupanca | carteira | corretora | outra'),
    }

    if method == 'post':
        campos['id_usuario'] = fields.Integer(
            required=True, description='ID do usuário dono da conta')
        campos['saldo_abertura'] = NullableFloat(
            required=False, description='Saldo inicial (vira ajuste)')

    if method == 'put':
        campos['id_conta'] = fields.Integer(
            required=True, description='ID da conta')

    return api.model(f'Conta_{method}', campos)
