from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_fatura_item_model import generate_fatura_item_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_fatura_item_facade import (
    ControleiFaturaItemFacade as item_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace(
    'controlei-fatura-item',
    description='Linhas avulsas de fatura (encargo/estorno/abertura)')


# ---------------------------->>
# Model
# ---------------------------->>
post_fatura_item_model = generate_fatura_item_model(api, "post")


model_get_fatura_item = api.parser().add_argument(
    name='id_fatura_item',
    type=int,
    help="ID do item"
).add_argument(
    name='id_fatura',
    type=int,
    help="ID da fatura"
).add_argument(
    name='id_compra',
    type=int,
    help="ID da compra (estorno)"
).add_argument(
    name='tipo',
    type=str,
    help="abertura | encargo | estorno | credito"
)

model_delete_fatura_item = api.parser().add_argument(
    name='id_fatura_item',
    type=int,
    required=True,
    help="ID do item"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class FaturaItemCollection(Resource):
    @api.expect(model_get_fatura_item, validate=True)
    def get(self):
        """Obtém itens avulsos de fatura"""
        result = item_f().obter_fatura_item(
            id_fatura_item=request.args.get('id_fatura_item'),
            id_fatura=request.args.get('id_fatura'),
            id_compra=request.args.get('id_compra'),
            tipo=request.args.get('tipo'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_fatura_item_model, validate=True)
    def post(self):
        """Cria uma linha avulsa na fatura (encargo, estorno, etc.)"""
        parm_dict = request.get_json()

        id_item = item_f().criar_fatura_item(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, {'id_fatura_item': id_item})
        )

    @api.expect(model_delete_fatura_item, validate=True)
    def delete(self):
        """Apaga uma linha avulsa de fatura"""
        item_f().apagar_fatura_item(request.args.get('id_fatura_item'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
