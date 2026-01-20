from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_receita_model import generate_receita_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_receita_facade import (
    ControleiReceitaFacade as rec_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-receita',
                description='Tabela de receita de usuário')


# ---------------------------->>
# Model
# ---------------------------->>
put_receita_model = generate_receita_model(api, "put")
post_receita_model = generate_receita_model(api, "post")


model_get_income = api.parser().add_argument(
    name='id_receita',
    type=int,
    help="ID da receita"
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
    name='id_receita',
    type=int,
    help="ID da receita",
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
class ControleiMeioPagamento(Resource):
    @api.expect(model_get_income, validate=True)
    def get(self):
        """Obtém uma ou todas as receitas do usuário"""
        id_receita = request.args.get('id_receita')
        ch_rede = request.args.get('ch_rede')
        tipo_filtro = request.args.get('tipoFiltro')
        mes_inicial = request.args.get('mesInicial')
        mes_final = request.args.get('mesFinal')
        ano = request.args.get('ano')
        data_dia = request.args.get('dataDia')
        result = rec_f().obter_receita(
            id_receita, ch_rede,
            tipo_filtro, mes_inicial,
            mes_final, ano, data_dia)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_receita_model, validate=True)
    def post(self):
        """Cria uma nova receita pro usuario"""
        parm_dict = request.get_json()

        id_receita = rec_f().criar_receita(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_receita': id_receita})
        )

    @api.expect(put_receita_model, validate=True)
    def put(self):
        """Atualiza uma receita de um usuário"""
        parm_dict = request.get_json()

        rec_f().atualizar_receita(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )

    @api.expect(model_delete_income, validate=True)
    def delete(self):
        """Deleta uma receita de um usuário"""
        id_receita = request.args.get('id_receita')
        ch_rede = request.args.get('ch_rede')
        rec_f().apagar_receita(
            id_receita, ch_rede)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
