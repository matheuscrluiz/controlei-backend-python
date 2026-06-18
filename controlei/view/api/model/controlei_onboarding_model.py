from flask_restx import fields


def generate_onboarding_model(api):
    """Payload do onboarding: conta + saldo de abertura + cartão opcional."""
    cartao = api.model('OnboardingCartao', {
        'apelido': fields.String(required=True,
                                 description='Apelido do cartão'),
        'funcao': fields.String(
            required=True, description='credito | debito | multiplo'),
        'bandeira': fields.String(required=False),
        'ultimos4': fields.String(required=False),
        'limite': fields.Float(required=False),
        'dia_fechamento': fields.Integer(required=False),
        'dia_vencimento': fields.Integer(required=False),
    })

    return api.model('Onboarding_post', {
        'id_usuario': fields.Integer(required=True,
                                     description='ID do usuário'),
        'apelido': fields.String(
            required=True, description='Apelido da conta'),
        'id_instituicao': fields.Integer(
            required=False, description='Instituição da conta'),
        'tipo': fields.String(
            required=False, description='corrente | poupanca | carteira ...'),
        'saldo_abertura': fields.Float(
            required=False,
            description='Saldo inicial (vira lançamento ajuste)'),
        'cartao': fields.Nested(
            cartao, required=False, allow_null=True, skip_none=True),
    })
