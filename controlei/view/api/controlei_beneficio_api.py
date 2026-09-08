from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_beneficio_model import generate_beneficio_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_beneficio_facade import (
    ControleiBeneficioFacade as ben_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-beneficio',
                description='Benefícios (VA, VR, VT...) — módulo apartado '
                            'do patrimônio')


# ---------------------------->>
# Models
# ---------------------------->>
post_beneficio_model = generate_beneficio_model(api, "post")
put_beneficio_model = generate_beneficio_model(api, "put")
movimentar_model = generate_beneficio_model(api, "movimentar")
put_mov_model = generate_beneficio_model(api, "put_mov")

p_listar = api.parser().add_argument(
    name='id_usuario', type=int, required=True, help="ID do usuário")

p_deletar = api.parser().add_argument(
    name='id_beneficio', type=int, required=True, help="ID do benefício")

p_extrato = api.parser().add_argument(
    name='id_beneficio', type=int, required=True, help="ID do benefício"
).add_argument(
    name='competencia', type=str,
    help="Mês (YYYY-MM-DD, qualquer dia). Padrão: mês atual")

p_deletar_mov = api.parser().add_argument(
    name='id_beneficio_mov', type=int, required=True,
    help="ID do movimento")


# ---------------------------->>
# Rotas
# ---------------------------->>

@api.route('')
class BeneficioCollection(Resource):
    @api.expect(p_listar, validate=True)
    def get(self):
        """Benefícios do usuário (saldo, gasto do mês, 'por dia')"""
        result = ben_f().listar(request.args.get('id_usuario'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))

    @api.expect(post_beneficio_model, validate=True)
    def post(self):
        """Cria um benefício"""
        result = ben_f().criar(request.get_json())
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))

    @api.expect(put_beneficio_model, validate=True)
    def put(self):
        """Edita um benefício"""
        ben_f().atualizar(request.get_json())
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, None))

    @api.expect(p_deletar, validate=True)
    def delete(self):
        """Exclui um benefício (e seus movimentos)"""
        ben_f().deletar(request.args.get('id_beneficio'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, None))


@api.route('/extrato')
class BeneficioExtrato(Resource):
    @api.expect(p_extrato, validate=True)
    def get(self):
        """Extrato do mês + resumo + histórico 6 meses + comparativo"""
        result = ben_f().extrato(
            request.args.get('id_beneficio'),
            request.args.get('competencia'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, result))


@api.route('/movimentar')
class BeneficioMovimentar(Resource):
    @api.expect(movimentar_model, validate=True)
    def post(self):
        """Registra recarga ou gasto"""
        ben_f().movimentar(request.get_json())
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, None))

    @api.expect(put_mov_model, validate=True)
    def put(self):
        """Edita um movimento"""
        ben_f().atualizar_movimento(request.get_json())
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, None))

    @api.expect(p_deletar_mov, validate=True)
    def delete(self):
        """Exclui um movimento"""
        ben_f().deletar_movimento(request.args.get('id_beneficio_mov'))
        return jsonify(get_dict_retorno_endpoint(
            TIP_RETORNO_SUCESS, MSG_SUCESSO, None))
