from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_investimento_model import (
    generate_investimento_model)
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_instituicao_facade import (
    ControleiInstituicaoFacade as inst_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-instituicao',
                description='Tabela de instituições')


# ---------------------------->>
# Model
# ---------------------------->>
put_investimento_model = generate_investimento_model(api, "put")
post_investimento_model = generate_investimento_model(api, "post")


model_get_investiment = api.parser().add_argument(
    name='id_instituicao',
    type=int,
    help="ID do investimento"
)


model_delete_investiment = api.parser().add_argument(
    name='id_investimento',
    type=int,
    help="ID da investimento",
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
    @api.expect(model_get_investiment, validate=True)
    def get(self):
        """Obtém um ou todos investimentos do usuário"""
        id_instituicao = request.args.get('id_instituicao')

        result = inst_f().obter_instituicao(
            id_instituicao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_investimento_model, validate=True)
    def post(self):
        """Cria um novo investimento pro usuario"""
        parm_dict = request.get_json()

        id_investimento = inv_f().criar_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_investimento': id_investimento})
        )

    @api.expect(put_investimento_model, validate=True)
    def put(self):
        """Atualiza um investimento de um usuário"""
        parm_dict = request.get_json()

        inv_f().atualizar_investimento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_investiment, validate=True)
    def delete(self):
        """Deleta um investimento de um usuário"""
        id_investimento = request.args.get('id_investimento')
        ch_rede = request.args.get('ch_rede')
        inv_f().apagar_investimento(
            id_investimento, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
