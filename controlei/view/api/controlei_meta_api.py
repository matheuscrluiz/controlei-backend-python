from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_meta_model import generate_meta_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_meta_facade import (
    ControleiMetaFacade as meta_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-meta',
                description='Tabela de meta de usuário')


# ---------------------------->>
# Model
# ---------------------------->>
put_meta_model = generate_meta_model(api, "put")
post_meta_model = generate_meta_model(api, "post")


model_get_goal = api.parser().add_argument(
    name='id_meta',
    type=int,
    help="ID da meta"
).add_argument(
    name='ch_rede',
    type=str,
    help="Chave de rede do usuário",
    required=True
)


model_delete_goal = api.parser().add_argument(
    name='id_meta',
    type=int,
    help="ID da meta",
    required=True
).add_argument(
    name='ch_rede',
    type=int,
    help="Chave de rede do usuário",
    required=True
)

model_relatorio_saldo_mensal = api.parser().add_argument(
    name='ch_rede',
    type=str,
    help="Chave de rede do usuário",
    required=True
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiMeta(Resource):
    @api.expect(model_get_goal, validate=True)
    def get(self):
        """Obtém uma ou todas as metas do usuário"""
        id_meta = request.args.get('id_meta')
        ch_rede = request.args.get('ch_rede')
        result = meta_f().obter_meta(
            id_meta, ch_rede,)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_meta_model, validate=True)
    def post(self):
        """Cria uma nova meta pro usuario"""
        parm_dict = request.get_json()

        id_meta = meta_f().criar_meta(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_meta': id_meta})
        )

    @api.expect(put_meta_model, validate=True)
    def put(self):
        """Atualiza uma meta de um usuário"""
        parm_dict = request.get_json()

        meta_f().atualizar_meta(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_goal, validate=True)
    def delete(self):
        """Deleta uma meta de um usuário"""
        id_meta = request.args.get('id_meta')
        ch_rede = request.args.get('ch_rede')
        meta_f().apagar_meta(
            id_meta, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )


@api.route('/relatorio-saldo-mensal')
class ControleiMetaRelatoriSaldoMensal(Resource):
    @api.expect(model_relatorio_saldo_mensal, validate=True)
    def get(self):
        """Obtém relatório de saldo mensal, aporte e disponível para aporte"""
        ch_rede = request.args.get('ch_rede')
        result = meta_f().obter_relatorio_saldo_mensal(ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )
