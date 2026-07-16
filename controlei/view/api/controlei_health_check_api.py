import os

from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-health-check', description='Health Check')


# ---------------------------->>
# Rotas
# ---------------------------->>
model_health = api.parser().add_argument(
    name='X-Cron-Secret', location='headers', required=True,
    help="Segredo do cron"
)


@api.route('')
class HealthCheck(Resource):
    @api.expect(model_health)
    def get(self):
        """Health check"""
        segredo = os.environ.get('CRON_SECRET')
        enviado = request.headers.get('X-Cron-Secret')

        if not segredo or enviado != segredo:
            return {'erro': 'Não autorizado'}, 401
        result = {"result": "Healthy"}

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )
