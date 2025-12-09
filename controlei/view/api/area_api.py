# coding: utf-8
from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace

from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from .api_model import MODEL_AREA
from ...model.facade.area_facade import AreaFacade as area_f
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('area', description='area')

# ---------------------------->>
# Model
# ---------------------------->>
model_api_area = api.model('model_area', MODEL_AREA)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ResourceArea(Resource):

    def get(self):

        result = area_f().obter_area()

        return jsonify(
            get_dict_retorno_endpoint(TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(model_api_area, validate=True)
    def post(self):

        result = area_f().criar_area(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(model_api_area, validate=True)
    def put(self):

        area_f().alterar_area(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(TIP_RETORNO_SUCESS,  MSG_SUCESSO, None)
        )

    @api.expect(model_api_area, validate=True)
    def delete(self):

        area_f().apagar_area(request.get_json())

        return jsonify(
            get_dict_retorno_endpoint(TIP_RETORNO_SUCESS,  MSG_SUCESSO, None)
        )
