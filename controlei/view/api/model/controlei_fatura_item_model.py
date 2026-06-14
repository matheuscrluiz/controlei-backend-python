from flask_restx import fields


def generate_fatura_item_model(api, method):
    """
    Model Flask-RESTX da linha avulsa de fatura.
      - post: id_fatura + tipo + valor (positivo) obrigatórios;
              descricao e id_compra opcionais.
    tipo: abertura | encargo | estorno | credito
    """
    if method == 'post':
        return api.model('FaturaItem_post', {
            'id_fatura': fields.Integer(
                required=True, description='ID da fatura'),
            'tipo': fields.String(
                required=True,
                description='abertura | encargo | estorno | credito'),
            'valor': fields.Float(
                required=True,
                description='Valor positivo (o sinal vem do tipo)'),
            'descricao': fields.String(
                required=False, description='Descrição do item'),
            'id_compra': fields.Integer(
                required=False, description='Compra relacionada (estorno)'),
        })

    return api.model(f'FaturaItem_{method}', {})
