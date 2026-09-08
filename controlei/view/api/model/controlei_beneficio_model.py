from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger,
    NullableFloat,
    NullableString,
)


def generate_beneficio_model(api, acao):
    """
    Models por ação:
      - post: cria o benefício (id_usuario + dsc; tipo/cor/dia opcionais).
      - put       : edita (id_beneficio + campos).
      - movimentar: recarga ou gasto (id_beneficio + tipo + valor; data/desc
                    opcionais).
      - put_mov   : edita um movimento (id_beneficio_mov + campos).

    Campos opcionais usam tipos Nullable* para aceitar `null` do frontend.
    """
    if acao == 'post':
        return api.model('Beneficio_post', {
            'id_usuario': fields.Integer(required=True,
                                         description='ID do usuário'),
            'dsc_beneficio': fields.String(
                required=True, description='Nome (ex.: Vale-alimentação)'),
            'tipo': NullableString(
                required=False,
                description='va | vr | vt | presente | outro'),
            'cor': NullableString(required=False, description='Cor hex'),
            'dia_recarga': NullableInteger(
                required=False, description='Dia da recarga (1..31)'),
        })

    if acao == 'put':
        return api.model('Beneficio_put', {
            'id_beneficio': fields.Integer(required=True,
                                           description='ID do benefício'),
            'dsc_beneficio': NullableString(required=False,
                                            description='Nome'),
            'tipo': NullableString(required=False, description='Tipo'),
            'cor': NullableString(required=False, description='Cor hex'),
            'dia_recarga': NullableInteger(required=False,
                                           description='Dia da recarga'),
        })

    if acao == 'movimentar':
        return api.model('Beneficio_movimentar', {
            'id_beneficio': fields.Integer(required=True,
                                           description='ID do benefício'),
            'tipo': fields.String(required=True,
                                  description='recarga | gasto'),
            'valor': fields.Float(required=True,
                                  description='Valor (positivo)'),
            'data': NullableString(required=False,
                                   description='YYYY-MM-DD (padrão: hoje)'),
            'descricao': NullableString(required=False,
                                        description='Descrição'),
        })

    if acao == 'put_mov':
        return api.model('Beneficio_put_mov', {
            'id_beneficio_mov': fields.Integer(
                required=True, description='ID do movimento'),
            'valor': NullableFloat(required=False, description='Valor'),
            'data': NullableString(required=False,
                                   description='YYYY-MM-DD'),
            'descricao': NullableString(required=False,
                                        description='Descrição'),
        })
