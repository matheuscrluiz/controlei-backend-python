from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_lancamento_model import generate_lancamento_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_lancamento_facade import (
    ControleiLancamentoFacade as lanc_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-lancamento',
                description='Lançamentos (movimentam o saldo)')


# ---------------------------->>
# Model
# ---------------------------->>
post_lancamento_model = generate_lancamento_model(api, "post")
put_lancamento_model = generate_lancamento_model(api, "put")


model_get_lancamento = api.parser().add_argument(
    name='id_lancamento', type=int, help="ID do lançamento"
).add_argument(
    name='id_conta', type=int, help="ID da conta"
).add_argument(
    name='id_usuario', type=int, help="ID do usuário"
).add_argument(
    name='natureza', type=str,
    help="receita | despesa | transferencia | ajuste"
).add_argument(
    name='status', type=str, help="efetivado | previsto"
).add_argument(
    name='data_inicio', type=str, help="Início do período (YYYY-MM-DD)"
).add_argument(
    name='data_fim', type=str, help="Fim do período (YYYY-MM-DD)"
)

model_confirmar_lancamento = api.parser().add_argument(
    name='id_lancamento', type=int, required=True, help="ID do lançamento"
).add_argument(
    name='valor', type=float, required=False,
    help="Valor informado ao confirmar (recorrência variável)"
)

model_delete_lancamento = api.parser().add_argument(
    name='id_lancamento', type=int, required=True, help="ID do lançamento"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class LancamentoCollection(Resource):
    @api.expect(model_get_lancamento, validate=True)
    def get(self):
        """Obtém lançamentos (extrato, com vários filtros)"""
        result = lanc_f().obter_lancamento(
            id_lancamento=request.args.get('id_lancamento'),
            id_conta=request.args.get('id_conta'),
            id_usuario=request.args.get('id_usuario'),
            natureza=request.args.get('natureza'),
            status=request.args.get('status'),
            data_inicio=request.args.get('data_inicio'),
            data_fim=request.args.get('data_fim'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_lancamento_model, validate=True)
    def post(self):
        """Cria um lançamento (move o saldo)"""
        parm_dict = request.get_json()

        id_lancamento = lanc_f().criar_lancamento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO,
                {'id_lancamento': id_lancamento})
        )

    @api.expect(put_lancamento_model, validate=True)
    def put(self):
        """Atualiza um lançamento"""
        parm_dict = request.get_json()

        lanc_f().atualizar_lancamento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )

    @api.expect(model_delete_lancamento, validate=True)
    def delete(self):
        """Deleta um lançamento"""
        lanc_f().deletar_lancamento(request.args.get('id_lancamento'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )


@api.route('/confirmar')
class LancamentoConfirmar(Resource):
    @api.expect(model_confirmar_lancamento, validate=True)
    def post(self):
        """Confirma um lançamento previsto (gerado por recorrência)"""
        lanc_f().confirmar_lancamento(
            request.args.get('id_lancamento'),
            request.args.get('valor'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
