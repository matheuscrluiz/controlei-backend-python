from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_onboarding_model import generate_onboarding_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_onboarding_facade import (
    ControleiOnboardingFacade as onb_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-onboarding',
                description='Primeira configuração do usuário')


# ---------------------------->>
# Model
# ---------------------------->>
post_onboarding_model = generate_onboarding_model(api)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class OnboardingResource(Resource):
    @api.expect(post_onboarding_model, validate=True)
    def post(self):
        """Cria conta + saldo de abertura + (opcional) primeiro cartão"""
        parm_dict = request.get_json()

        resultado = onb_f().realizar_onboarding(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )
