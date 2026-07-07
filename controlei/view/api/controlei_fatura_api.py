from flask import jsonify, request
import os
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

model_fechar_auto = api.parser().add_argument(
    name='X-Cron-Secret', location='headers', required=True,
    help="Segredo do cron (igual à env CRON_SECRET)"
)

model_notificar = api.parser().add_argument(
    name='X-Cron-Secret', location='headers', required=True,
    help="Segredo do cron (igual à env CRON_SECRET)"
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


@api.route('/fechar-automatico')
class FaturasFecharAutomatico(Resource):
    @api.expect(model_fechar_auto)
    def post(self):
        """Fecha (aberta -> fechada) faturas cujo fechamento já chegou.
        Uso do cron. Protegido por header X-Cron-Secret == env CRON_SECRET."""
        segredo = os.environ.get('CRON_SECRET')
        enviado = request.headers.get('X-Cron-Secret')

        if not segredo or enviado != segredo:
            return {'erro': 'Não autorizado'}, 401

        resultado = fatura_f().fechar_faturas_do_dia()

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )


@api.route('/notificar')
class FaturasNotificar(Resource):
    @api.expect(model_notificar)
    def post(self):
        """Envia e-mails de fatura (fechada / a vencer / vencida).
        Uso do cron. Protegido por header X-Cron-Secret == env CRON_SECRET."""
        segredo = os.environ.get('CRON_SECRET')
        enviado = request.headers.get('X-Cron-Secret')

        if not segredo or enviado != segredo:
            return {'erro': 'Não autorizado'}, 401

        resultado = fatura_f().processar_notificacoes_faturas()

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
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
