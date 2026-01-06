from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_rendimento_investimento_model import (
    generate_rendimento_investimento_model)
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_rendimento_investimento_facade import (
    ControleiRendimentoInvestimentoFacade as rend_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-rendimento-investimento',
                description='Tabela de rendimento de investimentos')


# ---------------------------->>
# Model
# ---------------------------->>
put_rendimento_investimento_model = generate_rendimento_investimento_model(
    api, "put")
post_rendimento_investimento_model = generate_rendimento_investimento_model(
    api, "post")


model_get_yield_investiment = api.parser().add_argument(
    name='id_rendimento',
    type=int,
    help="ID do rendimento"
).add_argument(
    name='id_investimento',
    type=int,
    help="ID do investimento"
).add_argument(
    name='ch_rede',
    type=str,
    help="Chave de rede do usuário",
    required=True
)


model_delete_investiment_yield = api.parser().add_argument(
    name='id_rendimento',
    type=int,
    help="ID do rendimento",
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
    @api.expect(model_get_yield_investiment, validate=True)
    def get(self):
        """Obtém um ou todos aportes do usuário"""
        id_rendimento = request.args.get('id_rendimento')
        id_investimento = request.args.get('id_investimento')
        ch_rede = request.args.get('ch_rede')

        result = rend_f().obter_rendimento_investimento(
            id_rendimento,
            id_investimento,
            ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_rendimento_investimento_model, validate=True)
    def post(self):
        """Cria um novo aporte de um investimento do usuario"""
        parm_dict = request.get_json()

        id_aporte = rend_f().criar_rendimento_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_aporte': id_aporte})
        )

    @api.expect(put_rendimento_investimento_model, validate=True)
    def put(self):
        """Atualiza um investimento de um usuário"""
        parm_dict = request.get_json()

        rend_f().atualizar_rendimento_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_investiment_yield, validate=True)
    def delete(self):
        """Deleta um investimento de um usuário"""
        id_rendimento = request.args.get('id_rendimento')
        ch_rede = request.args.get('ch_rede')
        rend_f().apagar_rendimento_investimento(
            id_rendimento, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
