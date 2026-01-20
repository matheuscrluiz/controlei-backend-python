from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_despesa_model import generate_despesa_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_despesa_facade import (
    ControleiDespesaFacade as desp_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-despesa',
                description='Tabela de despesa de usuário')


# ---------------------------->>
# Model
# ---------------------------->>
put_despesa_model = generate_despesa_model(api, "put")
post_despesa_model = generate_despesa_model(api, "post")


model_get_expenses = api.parser().add_argument(
    name='id_despesa',
    type=int,
    help="ID da despesa"
).add_argument(
    name='ch_rede',
    type=str,
    help="Chave de rede do usuário",
    required=True
).add_argument(
    name='tipoFiltro',
    type=str,
    choices=['DIA', 'MES', 'ANO'],
    required=True,
    help='Tipo de filtro'
) .add_argument(
    name='dataDia',
    type=str,
).add_argument(
    name='mesInicial',
    type=str,
).add_argument(
    name='mesFinal',
    type=str,
).add_argument(
    name='ano',
    type=str,
)


model_delete_income = api.parser().add_argument(
    name='id_despesa',
    type=int,
    help="ID da despesa",
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
class ControleiDespesas(Resource):
    @api.expect(model_get_expenses, validate=True)
    def get(self):
        """Obtém uma ou todas as depesas do usuário"""
        id_despesa = request.args.get('id_despesa')
        ch_rede = request.args.get('ch_rede')
        tipo_filtro = request.args.get('tipoFiltro')
        mes_inicial = request.args.get('mesInicial')
        mes_final = request.args.get('mesFinal')
        ano = request.args.get('ano')
        data_dia = request.args.get('dataDia')
        result = desp_f().obter_despesa(
            id_despesa, ch_rede,
            tipo_filtro, mes_inicial,
            mes_final, ano, data_dia)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_despesa_model, validate=True)
    def post(self):
        """Cria uma nova despesa pro usuario"""
        parm_dict = request.get_json()

        id_despesa = desp_f().criar_despesa(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_despesa': id_despesa})
        )

    @api.expect(put_despesa_model, validate=True)
    def put(self):
        """Atualiza uma receita de um usuário"""
        parm_dict = request.get_json()

        desp_f().atualizar_despesa(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_income, validate=True)
    def delete(self):
        """Deleta uma receita de um usuário"""
        id_despesa = request.args.get('id_despesa')
        ch_rede = request.args.get('ch_rede')
        desp_f().apagar_despesa(
            id_despesa, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
