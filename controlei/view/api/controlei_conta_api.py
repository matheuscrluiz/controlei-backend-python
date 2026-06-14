from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_conta_model import generate_conta_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_conta_facade import (
    ControleiContaFacade as conta_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-conta', description='Contas do usuário')


# ---------------------------->>
# Model
# ---------------------------->>
put_conta_model = generate_conta_model(api, "put")
post_conta_model = generate_conta_model(api, "post")


model_get_conta = api.parser().add_argument(
    name='id_conta',
    type=int,
    help="ID da conta"
).add_argument(
    name='id_usuario',
    type=int,
    help="ID do usuário (lista as contas dele)"
)

model_delete_conta = api.parser().add_argument(
    name='id_conta',
    type=int,
    help="ID da conta",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ContaCollection(Resource):
    @api.expect(model_get_conta, validate=True)
    def get(self):
        """Obtém contas (todas, por id, ou as de um usuário)"""
        id_conta = request.args.get('id_conta')
        id_usuario = request.args.get('id_usuario')

        result = conta_f().obter_conta(
            id_conta=id_conta, id_usuario=id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_conta_model, validate=True)
    def post(self):
        """Cria uma nova conta"""
        parm_dict = request.get_json()

        id_conta = conta_f().criar_conta(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_conta': id_conta})
        )

    @api.expect(put_conta_model, validate=True)
    def put(self):
        """Atualiza uma conta existente"""
        parm_dict = request.get_json()

        conta_f().atualizar_conta(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_conta, validate=True)
    def delete(self):
        """Deleta uma conta"""
        id_conta = request.args.get('id_conta')
        conta_f().deletar_conta(id_conta)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )


@api.route('/<int:id_conta>')
class ContaDetail(Resource):
    def get(self, id_conta):
        """Obtém uma conta por ID"""
        result = conta_f().obter_conta(id_conta=id_conta)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )
