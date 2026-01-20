from flask_restx import Model, fields, Namespace


def generate_despesa_model(api: Namespace, type: str) -> Model:
    model = {
        'id_categoria': fields.Integer(
            required=True,
            description="ID da categoria"
        ),
        'id_meio_pagamento': fields.Integer(
            required=True,
            description="ID da forma de pagamento"
        ),
        'ch_rede': fields.String(
            required=True,
            description="Chave de rede do usuário"
        ),
        'dsc_despesa': fields.String(
            required=False,
            description="Descrição da despesa"
        ),
        'valor_total': fields.Float(
            required=True,
            description="Valor da despesa"
        ),
        'data_despesa': fields.Date(
            required=True,
            description="Data da despesa"
        ),
        'despesa_recorrente': fields.String(
            required=False,
            description="Indica se a despesa é recorrente (S/N)"
        ),
        'parcelada': fields.String(
            required=False,
            description="Indica se despesa é parcelada"
        ),
        'pago': fields.String(
            required=False,
            description="Indica se despesa foi paga"
        ),
    }

    if type == 'post':
        return api.model(name='post_despesa_model', model=model)

    model.update({
        'id_despesa': fields.Integer(
            required=True,
            description="ID da despesa"
        ),
    })

    return api.model(name='put_despesa_model', model=model)
