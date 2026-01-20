from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_instituicao_model import (
    generate_instituicao_model)
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
put_instituicao_model = generate_instituicao_model(api, "put")
post_instituicao_model = generate_instituicao_model(api, "post")


model_get_instituicao = api.parser().add_argument(
    name='id_instituicao',
    type=int,
    help="ID da instituição"
)


model_delete_instituicao = api.parser().add_argument(
    name='id_instituicao',
    type=int,
    help="ID da instituição",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiInstituicao(Resource):
    @api.expect(model_get_instituicao, validate=True)
    def get(self):
        """Obtém instituições bancárias"""
        id_instituicao = request.args.get('id_instituicao')

        result = inst_f().obter_instituicao(
            id_instituicao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_instituicao_model, validate=True)
    def post(self):
        """Cria uma nova instituticão"""
        parm_dict = request.get_json()

        id_instituicao = inst_f().criar_instituicao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_instituicao': id_instituicao})
        )

    @api.expect(put_instituicao_model, validate=True)
    def put(self):
        """Atualiza uma instituição"""
        parm_dict = request.get_json()

        inst_f().atualizar_instituicao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_instituicao, validate=True)
    def delete(self):
        """Deleta uma instituição"""
        id_instituicao = request.args.get('id_instituicao')
        inst_f().apagar_instituicao(
            id_instituicao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
