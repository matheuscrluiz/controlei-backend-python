from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_cartao_model import generate_cartao_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_cartao_facade import (
    ControleiCartaoFacade as cartao_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-cartao', description='Cartões das contas')


# ---------------------------->>
# Model
# ---------------------------->>
put_cartao_model = generate_cartao_model(api, "put")
post_cartao_model = generate_cartao_model(api, "post")


model_get_cartao = api.parser().add_argument(
    name='id_cartao',
    type=int,
    help="ID do cartão"
).add_argument(
    name='id_conta',
    type=int,
    help="ID da conta (lista os cartões dela)"
).add_argument(
    name='id_usuario',
    type=int,
    help="ID do usuário (lista todos os cartões dele)"
)

model_delete_cartao = api.parser().add_argument(
    name='id_cartao',
    type=int,
    help="ID do cartão",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class CartaoCollection(Resource):
    @api.expect(model_get_cartao, validate=True)
    def get(self):
        """Obtém cartões (por id, por conta, ou por usuário)"""
        id_cartao = request.args.get('id_cartao')
        id_conta = request.args.get('id_conta')
        id_usuario = request.args.get('id_usuario')

        result = cartao_f().obter_cartao(
            id_cartao=id_cartao,
            id_conta=id_conta,
            id_usuario=id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_cartao_model, validate=True)
    def post(self):
        """Cria um novo cartão"""
        parm_dict = request.get_json()

        id_cartao = cartao_f().criar_cartao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_cartao': id_cartao})
        )

    @api.expect(put_cartao_model, validate=True)
    def put(self):
        """Atualiza um cartão existente"""
        parm_dict = request.get_json()

        cartao_f().atualizar_cartao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_cartao, validate=True)
    def delete(self):
        """Deleta um cartão"""
        id_cartao = request.args.get('id_cartao')
        cartao_f().deletar_cartao(id_cartao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )


@api.route('/<int:id_cartao>')
class CartaoDetail(Resource):
    def get(self, id_cartao):
        """Obtém um cartão por ID"""
        result = cartao_f().obter_cartao(id_cartao=id_cartao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )
