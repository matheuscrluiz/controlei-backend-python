from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_meta_movimentacao_model import (
    generate_meta_movimentacao_model)
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_meta_movimentacao_facade import (
    ControleiMetaMovimentacaoFacade as meta_movimentacao_f
)

# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-meta-movimentacao',
                description='Tabela de movimentação de meta do usuário')


# ---------------------------->>
# Model
# ---------------------------->>
put_meta_movimentacao_model = generate_meta_movimentacao_model(api, "put")
post_meta_movimentacao_model = generate_meta_movimentacao_model(api, "post")


model_get_movimentacao = api.parser().add_argument(
    name="ch_rede",
    type=str,
    help="Chave de rede do usuário",
    required=True
).add_argument(
    name='id_movimentacao',
    type=int,
    help="ID da movimentação"
).add_argument(
    name='id_meta',
    type=int,
    help="ID da meta"
)


model_delete_movimentacao = api.parser().add_argument(
    name='id_movimentacao',
    type=int,
    help="ID da movimentação",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiMetaMovimentacao(Resource):
    @api.expect(model_get_movimentacao, validate=True)
    def get(self):
        """Obtém uma ou todas as movimentações de meta"""
        id_movimentacao = request.args.get('id_movimentacao')
        id_meta = request.args.get('id_meta')
        ch_rede = request.args.get('ch_rede')
        result = meta_movimentacao_f().obter_movimentacao(
            ch_rede, id_movimentacao, id_meta)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_meta_movimentacao_model, validate=True)
    def post(self):
        """Cria uma nova movimentação de meta"""
        parm_dict = request.get_json()

        id_movimentacao = meta_movimentacao_f().criar_movimentacao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_movimentacao': id_movimentacao})
        )

    @api.expect(put_meta_movimentacao_model, validate=True)
    def put(self):
        """Atualiza uma movimentação de meta"""
        parm_dict = request.get_json()

        meta_movimentacao_f().atualizar_movimentacao(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_movimentacao, validate=True)
    def delete(self):
        """Deleta uma movimentação de meta"""
        id_movimentacao = request.args.get('id_movimentacao')
        meta_movimentacao_f().apagar_movimentacao(id_movimentacao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
