from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger,
    NullableFloat,
    NullableString,
    NullableNested,
)


def generate_onboarding_model(api):
    """Payload do onboarding: conta + saldo de abertura + cartão opcional."""
    cartao = api.model('OnboardingCartao', {
        'apelido': fields.String(required=True,
                                 description='Apelido do cartão'),
        'funcao': fields.String(
            required=True, description='credito | debito | multiplo'),
        'bandeira': NullableString(required=False),
        'ultimos4': NullableString(required=False),
        'limite': NullableFloat(required=False),
        'dia_fechamento': NullableInteger(required=False),
        'dia_vencimento': NullableInteger(required=False),
    })

    return api.model('Onboarding_post', {
        'id_usuario': fields.Integer(required=True,
                                     description='ID do usuário'),
        'apelido': fields.String(
            required=True, description='Apelido da conta'),
        'id_instituicao': NullableInteger(
            required=False, description='Instituição da conta'),
        'tipo': NullableString(
            required=False, description='corrente | poupanca | carteira ...'),
        'saldo_abertura': NullableFloat(
            required=False,
            description='Saldo inicial (vira lançamento ajuste)'),
        'cartao': NullableNested(
            cartao, required=False, allow_null=True, skip_none=True),
    })
