from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.login_model import (
    generate_login_model, generate_login_response_model)
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.login_facade import LoginFacade

# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('login', description='Autenticação de usuários')


# ---------------------------->>
# Models
# ---------------------------->>
login_model = generate_login_model(api)
login_response_model = generate_login_response_model(api)


# ---------------------------->>
# Rotas
# ---------------------------->>

@api.route('')
class LoginResource(Resource):
    @api.expect(login_model, validate=True)
    def post(self):
        """
        Realiza o login do usuário

        Recebe:
        - ch_rede: Chave de rede do usuário
        - senha: Senha do usuário

        Retorna:
        - Dados do usuário autenticado se bem-sucedido
        - Erro se credenciais forem inválidas
        """
        data = request.get_json()
        ch_rede = data.get('ch_rede')
        senha = data.get('senha')

        facade = LoginFacade()
        user_data = facade.login(ch_rede, senha)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                user_data)
        )
