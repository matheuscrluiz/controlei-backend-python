from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_orcamento_model import generate_orcamento_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_orcamento_facade import (
    ControleiOrcamentoFacade as orc_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-orcamento',
                description='Orçamento mensal por categoria')


# ---------------------------->>
# Model
# ---------------------------->>
post_orcamento_model = generate_orcamento_model(api, "post")
put_orcamento_model = generate_orcamento_model(api, "put")


model_get_orcamento = api.parser().add_argument(
    name='id_orcamento', type=int, help="ID do orçamento"
).add_argument(
    name='id_usuario', type=int, help="ID do usuário (lista os dele)"
).add_argument(
    name='id_categoria', type=int, help="ID da categoria"
)

model_delete_orcamento = api.parser().add_argument(
    name='id_orcamento', type=int, required=True, help="ID do orçamento"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiOrcamento(Resource):
    @api.expect(model_get_orcamento, validate=True)
    def get(self):
        """Obtém um ou todos os orçamentos"""
        result = orc_f().obter_orcamento(
            id_orcamento=request.args.get('id_orcamento'),
            id_usuario=request.args.get('id_usuario'),
            id_categoria=request.args.get('id_categoria'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_orcamento_model, validate=True)
    def post(self):
        """Cria um orçamento para uma categoria"""
        id_orcamento = orc_f().criar_orcamento(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO,
                {'id_orcamento': id_orcamento})
        )

    @api.expect(put_orcamento_model, validate=True)
    def put(self):
        """Atualiza o teto de um orçamento"""
        orc_f().atualizar_orcamento(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )

    @api.expect(model_delete_orcamento, validate=True)
    def delete(self):
        """Apaga um orçamento"""
        orc_f().apagar_orcamento(request.args.get('id_orcamento'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
