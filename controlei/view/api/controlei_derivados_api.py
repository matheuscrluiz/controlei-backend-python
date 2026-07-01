from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_derivados_facade import (
    ControleiDerivadosFacade as deriv_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-derivados',
                description='Leituras derivadas (saldo, dívida, fluxo, patrimônio)')


# ---------------------------->>
# Parsers
# ---------------------------->>
p_saldo = api.parser().add_argument(
    name='id_conta', type=int, required=True, help="ID da conta")

p_saldos = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário")

p_fatura_total = api.parser().add_argument(
    name='id_fatura', type=int, required=True, help="ID da fatura")

p_divida = api.parser().add_argument(
    name='id_cartao', type=int, help="ID do cartão"
).add_argument(
    name='id_usuario', type=int, help="ID do usuário")

p_fluxo = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário"
).add_argument(
    name='competencia', type=str, help="Mês (YYYY-MM)")

p_cofre = api.parser().add_argument(
    name='id_cofre', type=int, required=True, help="ID do cofre")

p_patrimonio = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário")

p_despesas_cat = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário"
).add_argument(
    name='data_inicio', type=str, required=True, help="Início (YYYY-MM-DD)"
).add_argument(
    name='data_fim', type=str, required=True, help="Fim (YYYY-MM-DD)")
# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('/saldo')
class Saldo(Resource):
    @api.expect(p_saldo, validate=True)
    def get(self):
        """Saldo de uma conta"""
        result = deriv_f().saldo_conta(request.args.get('id_conta'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, {'saldo': result}))


@api.route('/saldos')
class Saldos(Resource):
    @api.expect(p_saldos, validate=True)
    def get(self):
        """Saldo de cada conta do usuário"""
        result = deriv_f().saldos_por_conta(request.args.get('id_usuario'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))


@api.route('/fatura-total')
class FaturaTotal(Resource):
    @api.expect(p_fatura_total, validate=True)
    def get(self):
        """Total a pagar de uma fatura"""
        result = deriv_f().fatura_total(request.args.get('id_fatura'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, {'valor': result}))


@api.route('/divida')
class Divida(Resource):
    @api.expect(p_divida, validate=True)
    def get(self):
        """Dívida de cartão (por cartão ou por usuário)"""
        result = deriv_f().divida_cartao(
            id_cartao=request.args.get('id_cartao'),
            id_usuario=request.args.get('id_usuario'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, {'divida': result}))


@api.route('/fluxo')
class Fluxo(Resource):
    @api.expect(p_fluxo, validate=True)
    def get(self):
        """Fluxo mensal (receitas, despesas, resultado)"""
        result = deriv_f().fluxo_mensal(
            request.args.get('id_usuario'),
            request.args.get('competencia'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))


@api.route('/cofre-valor')
class CofreValor(Resource):
    @api.expect(p_cofre, validate=True)
    def get(self):
        """Valor atual de um cofre"""
        result = deriv_f().cofre_valor(request.args.get('id_cofre'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, {'valor': result}))


@api.route('/patrimonio')
class Patrimonio(Resource):
    @api.expect(p_patrimonio, validate=True)
    def get(self):
        """Patrimônio líquido do usuário (saldos + cofres - dívida)"""
        result = deriv_f().patrimonio_usuario(request.args.get('id_usuario'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))


@api.route('/despesas-por-categoria')
class DespesasPorCategoria(Resource):
    @api.expect(p_despesas_cat, validate=True)
    def get(self):
        """Gastos por categoria no período (conta + cartão)"""
        result = deriv_f().despesas_por_categoria(
            request.args.get('id_usuario'),
            request.args.get('data_inicio'),
            request.args.get('data_fim'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))
