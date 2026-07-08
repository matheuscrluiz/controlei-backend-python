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
    name='id_usuario',
    type=int,
    help="ID do usuário"
).add_argument(
    name='email',
    type=str,
    help="E-mail do usuário"
)

delete_usuario_model = api.parser().add_argument(
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
        """Obtém todos os usuários ou um usuário específico"""
        id_usuario = request.args.get('id_usuario')
        email = request.args.get('email')
        result = user_f().obter_usuario(id_usuario=id_usuario, email=email)

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
        id_usuario = request.args.get('id_usuario')
        user_f().deletar_usuario(id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )


model_get_pref = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário"
)


@api.route('/preferencias')
class UsuarioPreferencias(Resource):
    @api.expect(model_get_pref, validate=True)
    def get(self):
        """Preferências de e-mail do usuário."""
        id_usuario = request.args.get('id_usuario')
        result = user_f().obter_preferencias(id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    def put(self):
        """Atualiza as preferências de e-mail do usuário."""
        parm_dict = request.get_json()
        user_f().atualizar_preferencias(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


model_tg_link = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário"
)


@api.route('/telegram-link')
class UsuarioTelegramLink(Resource):
    @api.expect(model_tg_link, validate=True)
    def post(self):
        """Gera o deep link t.me para o usuário vincular o Telegram."""
        id_usuario = request.args.get('id_usuario')
        result = user_f().gerar_link_telegram(id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(model_tg_link, validate=True)
    def delete(self):
        """Desvincula o Telegram do usuário."""
        id_usuario = request.args.get('id_usuario')
        user_f().desvincular_telegram(id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/<int:id_usuario>')
class UsuarioDetail(Resource):
    def get(self, id_usuario):
        """Obtém um usuário por ID"""
        facade = user_f()
        usuario = facade.dao.get_user(id_usuario=id_usuario)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, usuario)
        )
