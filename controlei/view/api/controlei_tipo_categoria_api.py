from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_tipo_categoria_model import generate_tipo_categoria_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_tipo_categoria_facade import (
    ControleiTipoCategoriaFacade as tipo_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-tipo-categoria',
                description='Tabela de tipo de categoria')


# ---------------------------->>
# Model
# ---------------------------->>
put_tipo_categoria_model = generate_tipo_categoria_model(api, "put")
post_tipo_categoria_model = generate_tipo_categoria_model(api, "post")


model_get_type_category = api.parser().add_argument(
    name='id_tipo_categoria',
    type=int,
    help="ID do tipo da categoria"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiCategoria(Resource):
    @api.expect(model_get_type_category, validate=True)
    def get(self):
        """Obtém uma ou todas os tipos de categorias"""
        id_tipo_categoria = request.args.get('id_tipo_categoria')
        result = tipo_f().obter_tipo_categoria(id_tipo_categoria)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_tipo_categoria_model, validate=True)
    def post(self):
        """Cria um novo tipo de categoria"""
        parm_dict = request.get_json()

        id_tipo_categoria = tipo_f().criar_tipo_categoria(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_tipo_categoria': id_tipo_categoria})
        )

    @api.expect(put_tipo_categoria_model, validate=True)
    def put(self):
        """Atualiza um tipo de categoria existente"""
        parm_dict = request.get_json()

        tipo_f().atualizar_tipo_categoria(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
