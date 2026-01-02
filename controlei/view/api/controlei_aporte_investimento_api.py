from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_aporte_investimento_model import (
    generate_aporte_investimento_model)
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_aporte_investimento_facade import (
    ControleiAporteInvestimentoFacade as aport_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-aporte-investimento',
                description='Tabela de aporte de investimentos')


# ---------------------------->>
# Model
# ---------------------------->>
put_aporte_investimento_model = generate_aporte_investimento_model(
    api, "put")
post_aporte_investimento_model = generate_aporte_investimento_model(
    api, "post")


model_get_inject_investiment = api.parser().add_argument(
    name='id_aporte',
    type=int,
    help="ID do aporte"
).add_argument(
    name='ch_rede',
    type=str,
    help="Chave de rede do usuário",
    required=True
)


model_delete_investiment = api.parser().add_argument(
    name='id_aporte',
    type=int,
    help="ID da aporte",
    required=True
).add_argument(
    name='ch_rede',
    type=int,
    help="Chave de rede do usuário",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiMeioPagamento(Resource):
    @api.expect(model_get_inject_investiment, validate=True)
    def get(self):
        """Obtém um ou todos aportes do usuário"""
        id_aporte = request.args.get('id_aporte')
        ch_rede = request.args.get('ch_rede')

        result = aport_f().obter_aporte_investimento(
            id_aporte, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_aporte_investimento_model, validate=True)
    def post(self):
        """Cria um novo aporte de um investimento do usuario"""
        parm_dict = request.get_json()

        id_aporte = aport_f().criar_aporte_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_aporte': id_aporte})
        )

    @api.expect(put_aporte_investimento_model, validate=True)
    def put(self):
        """Atualiza um investimento de um usuário"""
        parm_dict = request.get_json()

        aport_f().atualizar_aporte_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_investiment, validate=True)
    def delete(self):
        """Deleta um investimento de um usuário"""
        id_aporte = request.args.get('id_aporte')
        ch_rede = request.args.get('ch_rede')
        aport_f().apagar_aporte_investimento(
            id_aporte, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
