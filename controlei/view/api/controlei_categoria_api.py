from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_categoria_model import generate_categoria_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_categoria_facade import (
    ControleiCategoriaFacade as cat_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-categoria', description='Tabela de categoria')


# ---------------------------->>
# Model
# ---------------------------->>
put_categoria_model = generate_categoria_model(api, "put")
post_categoria_model = generate_categoria_model(api, "post")


model_get_category = api.parser().add_argument(
    name='id_categoria',
    type=int,
    help="ID da categoria"
).add_argument(
    name='id_tipo_categoria',
    type=int,
    help="ID do tipo da categoria"
)
model_delete_category = api.parser().add_argument(
    name='id_categoria',
    type=int,
    required=True,
    help="ID da categoria"
).add_argument(
    name='id_tipo_categoria',
    type=int,
    required=True,
    help="ID do tipo da categoria"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiCategoria(Resource):
    @api.expect(model_get_category, validate=True)
    def get(self):
        """Obtém uma ou todas as categorias"""
        id_categoria = request.args.get('id_categoria')
        id_tipo_categoria = request.args.get('id_tipo_categoria')
        result = cat_f().obter_categoria(id_categoria, id_tipo_categoria)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_categoria_model, validate=True)
    def post(self):
        """Cria uma nova categoria"""
        parm_dict = request.get_json()

        id_categoria = cat_f().criar_categoria(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_categoria': id_categoria})
        )

    @api.expect(put_categoria_model, validate=True)
    def put(self):
        """Atualiza uma categoria existente"""
        parm_dict = request.get_json()

        cat_f().atualizar_categoria(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_category, validate=True)
    def delete(self):
        """Deleta uma categoria existente"""
        id_categoria = request.args.get('id_categoria')
        id_tipo_categoria = request.args.get('id_tipo_categoria')
        cat_f().apagar_categoria(id_categoria, id_tipo_categoria)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
