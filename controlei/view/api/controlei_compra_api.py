from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_compra_model import generate_compra_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_compra_facade import (
    ControleiCompraFacade as compra_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-compra', description='Compras no crédito')


# ---------------------------->>
# Model
# ---------------------------->>
post_compra_model = generate_compra_model(api, "post")
put_compra_model = generate_compra_model(api, "put")


model_get_compra = api.parser().add_argument(
    name='id_compra',
    type=int,
    help="ID da compra"
).add_argument(
    name='id_cartao',
    type=int,
    help="ID do cartão"
).add_argument(
    name='id_usuario',
    type=int,
    help="ID do usuário"
).add_argument(
    name='com_parcelas',
    type=bool,
    help="Inclui as parcelas de cada compra"
)

model_get_parcelas = api.parser().add_argument(
    name='id_compra',
    type=int,
    help="ID da compra"
).add_argument(
    name='id_fatura',
    type=int,
    help="ID da fatura"
)

model_delete_compra = api.parser().add_argument(
    name='id_compra',
    type=int,
    required=True,
    help="ID da compra"
)

model_cancelar_compra = api.parser().add_argument(
    name='id_compra',
    type=int,
    required=True,
    help="ID da compra a cancelar"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class CompraCollection(Resource):
    @api.expect(model_get_compra, validate=True)
    def get(self):
        """Obtém compras (por id, cartão ou usuário)"""
        com_parcelas = request.args.get('com_parcelas') in (
            'true', 'True', '1', True)

        result = compra_f().obter_compra(
            id_compra=request.args.get('id_compra'),
            id_cartao=request.args.get('id_cartao'),
            id_usuario=request.args.get('id_usuario'),
            com_parcelas=com_parcelas)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_compra_model, validate=True)
    def post(self):
        """Cria uma compra e gera suas parcelas nas faturas corretas"""
        parm_dict = request.get_json()

        id_compra = compra_f().criar_compra(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, {'id_compra': id_compra})
        )

    @api.expect(put_compra_model, validate=True)
    def put(self):
        """Atualiza descrição/categoria de uma compra"""
        parm_dict = request.get_json()

        compra_f().atualizar_compra(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )

    @api.expect(model_delete_compra, validate=True)
    def delete(self):
        """Deleta uma compra (e suas parcelas)"""
        compra_f().deletar_compra(request.args.get('id_compra'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/parcelas')
class ParcelaCollection(Resource):
    @api.expect(model_get_parcelas, validate=True)
    def get(self):
        """Lista parcelas (de uma compra ou de uma fatura)"""
        result = compra_f().obter_parcelas(
            id_compra=request.args.get('id_compra'),
            id_fatura=request.args.get('id_fatura'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )


@api.route('/cancelar')
class CompraCancelar(Resource):
    @api.expect(model_cancelar_compra, validate=True)
    def post(self):
        """Cancela a compra: remove parcelas não pagas e credita as pagas"""
        compra_f().cancelar_compra(request.args.get('id_compra'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
