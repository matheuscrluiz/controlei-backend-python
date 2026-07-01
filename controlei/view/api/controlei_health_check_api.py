from flask import jsonify
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


@api.route('')
class HealthCheck(Resource):
    def get(self):
        """Health check"""
        result = {"result": "Healthy"}

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )
