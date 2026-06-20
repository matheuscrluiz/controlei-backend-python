from flask_restx import fields
from controlei.util.restx_fields import NullableInteger, NullableString


def generate_instituicao_model(api, method):
    """
    Model Flask-RESTX da instituição.
      - post: dsc_instituicao obrigatório; cor/logo_slug/tipo opcionais;
              id_usuario opcional (nulo = compartilhada/seed).
      - put : id_instituicao obrigatório + os campos editáveis.
    """
    campos = {
        'dsc_instituicao': fields.String(
            required=True, description='Nome da instituição'),
        'cor': NullableString(
            required=False, description='Cor em hex, ex.: #8A05BE'),
        'logo_slug': NullableString(
            required=False, description='Identificador do logo, ex.: nubank'),
        'tipo': NullableString(
            required=False,
            description='banco | fintech | corretora | carteira'),
    }

    if method == 'post':
        campos['id_usuario'] = NullableInteger(
            required=False,
            description='Dono da instituição (nulo = compartilhada)')

    if method == 'put':
        campos['id_instituicao'] = fields.Integer(
            required=True, description='ID da instituição')

    return api.model(f'Instituicao_{method}', campos)
