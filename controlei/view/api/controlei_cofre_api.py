from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_cofre_model import generate_cofre_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_cofre_facade import (
    ControleiCofreFacade as cofre_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-cofre',
                description='Cofres (meta + investimento)')


# ---------------------------->>
# Model
# ---------------------------->>
post_cofre_model = generate_cofre_model(api, "post")
put_cofre_model = generate_cofre_model(api, "put")
valor_atual_model = generate_cofre_model(api, "valor_atual")
movimentar_model = generate_cofre_model(api, "movimentar")


model_get_cofre = api.parser().add_argument(
    name='id_cofre', type=int, help="ID do cofre"
).add_argument(
    name='id_conta', type=int, help="ID da conta"
).add_argument(
    name='id_usuario', type=int, help="ID do usuário"
)

model_delete_cofre = api.parser().add_argument(
    name='id_cofre', type=int, required=True, help="ID do cofre"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class CofreCollection(Resource):
    @api.expect(model_get_cofre, validate=True)
    def get(self):
        """Obtém cofres (com aportado e valor calculados)"""
        result = cofre_f().obter_cofre(
            id_cofre=request.args.get('id_cofre'),
            id_conta=request.args.get('id_conta'),
            id_usuario=request.args.get('id_usuario'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_cofre_model, validate=True)
    def post(self):
        """Cria um cofre"""
        id_cofre = cofre_f().criar_cofre(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, {'id_cofre': id_cofre})
        )

    @api.expect(put_cofre_model, validate=True)
    def put(self):
        """Atualiza um cofre"""
        cofre_f().atualizar_cofre(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )

    @api.expect(model_delete_cofre, validate=True)
    def delete(self):
        """Apaga um cofre (precisa estar zerado)"""
        cofre_f().deletar_cofre(request.args.get('id_cofre'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/valor-atual')
class CofreValorAtual(Resource):
    @api.expect(valor_atual_model, validate=True)
    def put(self):
        """Informa o valor de mercado do cofre (investimento)"""
        cofre_f().informar_valor_atual(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/aportar')
class CofreAportar(Resource):
    @api.expect(movimentar_model, validate=True)
    def post(self):
        """Aporta no cofre (baixa o saldo da conta)"""
        cofre_f().aportar(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/resgatar')
class CofreResgatar(Resource):
    @api.expect(movimentar_model, validate=True)
    def post(self):
        """Resgata do cofre (repõe o saldo da conta)"""
        cofre_f().resgatar(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
