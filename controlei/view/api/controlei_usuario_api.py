from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_usuario_model import generate_usuario_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_usuario_facade import (
    ControleiUserFacade as user_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-user', description='Tabela de usuários')


# ---------------------------->>
# Model
# ---------------------------->>
put_usuario_model = generate_usuario_model(api, "put")
post_usuario_model = generate_usuario_model(api, "post")


model_get_user = api.parser().add_argument(
    name='ch_rede',
    type=str,
    help="ch_rede do usuário"
)
delete_usuario_model = api.parser().add_argument(
    name='ch_rede',
    type=str,
    help="ch_rede do usuário",
    required=True
).add_argument(
    name='id_usuario',
    type=int,
    help="ID do usuário",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class UsuarioCollection(Resource):
    @api.expect(model_get_user, validate=True)
    def get(self):
        """Obtém todos usuários ou um usuário específico"""
        ch_rede = request.args.get('ch_rede')
        result = user_f().obter_usuario(ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_usuario_model, validate=True)
    def post(self):
        """Cria um novo usuário"""
        parm_dict = request.get_json()

        user_id = user_f().criar_usuario(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id': user_id})
        )

    @api.expect(put_usuario_model, validate=True)
    def put(self):
        """Atualiza um usuário existente"""
        parm_dict = request.get_json()

        user_f().atualizar_usuario(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(delete_usuario_model, validate=True)
    def delete(self):
        """Deleta um usuário"""
        facade = user_f()
        ch_rede = request.args.get('ch_rede')
        id_usuario = request.args.get('id_usuario')
        facade.deletar_usuario(id_usuario, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )


@api.route('/<int:id_usuario>')
class UsuarioDetail(Resource):
    def get(self, id_usuario):
        """Obtém um usuário por ID"""
        facade = user_f()
        usuario = facade.dao.get_user_by_id(id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, usuario)
        )
