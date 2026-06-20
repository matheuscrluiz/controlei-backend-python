from flask_restx import fields
from controlei.util.restx_fields import (
    NullableInteger,
    NullableString,
    NullableBoolean,
)


def generate_compra_model(api, method):
    """
    Model Flask-RESTX da compra.
      - post: id_cartao + dsc_compra + valor_total obrigatórios; data_compra,
              num_parcelas, id_categoria, pre_existente opcionais.
      - put : id_compra obrigatório; dsc_compra/id_categoria editáveis.
    """
    if method == 'post':
        return api.model('Compra_post', {
            'id_cartao': fields.Integer(
                required=True, description='ID do cartão (crédito)'),
            'dsc_compra': fields.String(
                required=True, description='Descrição da compra'),
            'valor_total': fields.Float(
                required=True, description='Valor total da compra'),
            'data_compra': NullableString(
                required=False, description='Data da compra (YYYY-MM-DD)'),
            'num_parcelas': NullableInteger(
                required=False, description='Nº de parcelas (1 = à vista)'),
            'id_categoria': NullableInteger(
                required=False, description='ID da categoria'),
            'pre_existente': NullableBoolean(
                required=False,
                description='Compra anterior ao app (onboarding)'),
        })

    if method == 'put':
        return api.model('Compra_put', {
            'id_compra': fields.Integer(
                required=True, description='ID da compra'),
            'dsc_compra': NullableString(
                required=False, description='Descrição da compra'),
            'id_categoria': NullableInteger(
                required=False, description='ID da categoria'),
        })

    return api.model(f'Compra_{method}', {})
