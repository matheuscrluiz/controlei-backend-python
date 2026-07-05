from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_fatura_model import generate_fatura_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_fatura_facade import (
    ControleiFaturaFacade as fatura_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-fatura', description='Faturas dos cartões')


# ---------------------------->>
# Model
# ---------------------------->>
post_fatura_model = generate_fatura_model(api, "post")
put_fatura_model = generate_fatura_model(api, "put")


model_get_fatura = api.parser().add_argument(
    name='id_fatura',
    type=int,
    help="ID da fatura"
).add_argument(
    name='id_cartao',
    type=int,
    help="ID do cartão"
).add_argument(
    name='status',
    type=str,
    help="aberta | fechada | paga"
).add_argument(
    name='competencia',
    type=str,
    help="Mês de referência (YYYY-MM)"
).add_argument(
    name='id_usuario',
    type=int,
    help="ID do usuário (todas as faturas dele)"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


model_a_vencer = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário"
).add_argument(
    name='dias', type=int, help="Janela em dias (default 7; inclui vencidas)"
)


@api.route('/a-vencer')
class FaturasAVencer(Resource):
    @api.expect(model_a_vencer, validate=True)
    def get(self):
        """Faturas não pagas a vencer (hoje..+dias) ou já vencidas."""
        result = fatura_f().obter_faturas_a_vencer(
            request.args.get('id_usuario'),
            request.args.get('dias'))
        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )


@api.route('')
class FaturaCollection(Resource):
    @api.expect(model_get_fatura, validate=True)
    def get(self):
        """Obtém faturas (por id, cartão, status, competência ou usuário)"""
        result = fatura_f().obter_fatura(
            id_fatura=request.args.get('id_fatura'),
            id_cartao=request.args.get('id_cartao'),
            status=request.args.get('status'),
            competencia=request.args.get('competencia'),
            id_usuario=request.args.get('id_usuario'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_fatura_model, validate=True)
    def post(self):
        """Obtém ou cria a fatura do cartão para a competência informada"""
        parm_dict = request.get_json()

        fatura = fatura_f().obter_ou_criar_fatura(
            parm_dict.get('id_cartao'), parm_dict.get('competencia'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, fatura)
        )

    @api.expect(put_fatura_model, validate=True)
    def put(self):
        """Atualiza o status de uma fatura"""
        parm_dict = request.get_json()

        fatura_f().atualizar_status_fatura(
            parm_dict.get('id_fatura'), parm_dict.get('status'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
