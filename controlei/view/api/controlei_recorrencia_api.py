from flask import jsonify, request
import os
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_recorrencia_model import generate_recorrencia_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_recorrencia_facade import (
    ControleiRecorrenciaFacade as rec_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-recorrencia',
                description='Recorrências (contas fixas, assinaturas)')


# ---------------------------->>
# Model
# ---------------------------->>
post_recorrencia_model = generate_recorrencia_model(api, "post")
put_recorrencia_model = generate_recorrencia_model(api, "put")


model_get_recorrencia = api.parser().add_argument(
    name='id_recorrencia', type=int, help="ID da recorrência"
).add_argument(
    name='id_usuario', type=int, help="ID do usuário"
).add_argument(
    name='ativa', type=bool, help="Somente ativas/inativas"
).add_argument(
    name='dia_do_mes', type=int, help="Dia do mês"
)

model_delete_recorrencia = api.parser().add_argument(
    name='id_recorrencia', type=int, required=True, help="ID da recorrência"
)

model_gerar = api.parser().add_argument(
    name='id_recorrencia', type=int, required=True, help="ID da recorrência"
).add_argument(
    name='data', type=str, help="Data da ocorrência (YYYY-MM-DD)"
)

model_gerar_todas = api.parser().add_argument(
    name='X-Cron-Secret', location='headers', required=True,
    help="Segredo do cron "
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class RecorrenciaCollection(Resource):
    @api.expect(model_get_recorrencia, validate=True)
    def get(self):
        """Obtém recorrências"""
        result = rec_f().obter_recorrencia(
            id_recorrencia=request.args.get('id_recorrencia'),
            id_usuario=request.args.get('id_usuario'),
            ativa=request.args.get('ativa'),
            dia_do_mes=request.args.get('dia_do_mes'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_recorrencia_model, validate=True)
    def post(self):
        """Cria uma recorrência"""
        id_rec = rec_f().criar_recorrencia(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, {'id_recorrencia': id_rec})
        )

    @api.expect(put_recorrencia_model, validate=True)
    def put(self):
        """Atualiza uma recorrência"""
        rec_f().atualizar_recorrencia(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )

    @api.expect(model_delete_recorrencia, validate=True)
    def delete(self):
        """Apaga uma recorrência"""
        rec_f().deletar_recorrencia(request.args.get('id_recorrencia'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/gerar')
class RecorrenciaGerar(Resource):
    @api.expect(model_gerar, validate=True)
    def post(self):
        """Gera a ocorrência do mês (lançamento previsto ou compra de 1x)"""
        resultado = rec_f().gerar_ocorrencia(
            request.args.get('id_recorrencia'),
            request.args.get('data'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, {'gerado': resultado})
        )


@api.route('/gerar-todas')
class RecorrenciaGerarTodas(Resource):
    @api.expect(model_gerar_todas)
    def post(self):
        """Gera o mês para TODAS as recorrências ativas (uso do cron).
        Protegido por header """
        segredo = os.environ.get('CRON_SECRET')
        enviado = request.headers.get('X-Cron-Secret')

        if not segredo or enviado != segredo:
            return {'erro': 'Não autorizado'}, 401

        resultado = rec_f().gerar_mes_todos()

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )
