from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger,
    NullableFloat,
    NullableString,
)


def generate_cofre_model(api, acao):
    """
    Models por ação:
      - post: cria o cofre (id_conta + dsc_cofre; alvo/prioridade opcionais).
      - put : edita (id_cofre + dsc_cofre; alvo/prioridade).
      - valor_atual: informa o valor de mercado (investimento).
      - movimentar : aporte/resgate (id_cofre + valor).

    Campos opcionais usam tipos Nullable* para aceitar `null` enviado pelo
    frontend (ver controlei.util.restx_fields).
    """
    if acao == 'post':
        return api.model('Cofre_post', {
            'id_conta': fields.Integer(required=True,
                                       description='ID da conta'),
            'dsc_cofre': fields.String(
                required=True, description='Descrição do cofre'),
            'valor_alvo': NullableFloat(
                required=False, description='Alvo (vira meta)'),
            'prioridade': NullableInteger(required=False,
                                          description='Prioridade'),
            'valor_atual_inform': NullableFloat(
                required=False, description='Valor de mercado (investimento)'),
        })

    if acao == 'put':
        return api.model('Cofre_put', {
            'id_cofre': fields.Integer(required=True,
                                       description='ID do cofre'),
            'dsc_cofre': NullableString(required=False,
                                        description='Descrição'),
            'valor_alvo': NullableFloat(required=False,
                                        description='Alvo'),
            'prioridade': NullableInteger(required=False,
                                          description='Prioridade'),
        })

    if acao == 'valor_atual':
        return api.model('Cofre_valor_atual', {
            'id_cofre': fields.Integer(required=True,
                                       description='ID do cofre'),
            'valor_atual_inform': fields.Float(
                required=True, description='Valor de mercado atual'),
            'data_valor_atual': NullableString(
                required=False, description='Data (YYYY-MM-DD)'),
        })

    if acao == 'movimentar':
        return api.model('Cofre_movimentar', {
            'id_cofre': fields.Integer(required=True,
                                       description='ID do cofre'),
            'valor': fields.Float(required=True,
                                  description='Valor (positivo)'),
            'data': NullableString(required=False,
                                   description='Data (YYYY-MM-DD)'),
            'descricao': NullableString(required=False,
                                        description='Descrição'),
        })

    return api.model(f'Cofre_{acao}', {})
