from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_transferencia_model import generate_transferencia_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_transferencia_facade import (
    ControleiTransferenciaFacade as transf_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-transferencia',
                description='Transferências (entre contas, pagar fatura)')


# ---------------------------->>
# Model
# ---------------------------->>
entre_contas_model = generate_transferencia_model(api, "entre_contas")
pagar_fatura_model = generate_transferencia_model(api, "pagar_fatura")


model_get_transferencia = api.parser().add_argument(
    name='id_transferencia', type=int, help="ID da transferência"
).add_argument(
    name='tipo', type=str,
    help="entre_contas | aporte | resgate | pagamento_fatura"
).add_argument(
    name='id_conta_origem', type=int, help="Conta de origem"
).add_argument(
    name='id_fatura', type=int, help="Fatura (pagamento)"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class TransferenciaCollection(Resource):
    @api.expect(model_get_transferencia, validate=True)
    def get(self):
        """Obtém transferências (por id, tipo, conta de origem ou fatura)"""
        result = transf_f().obter_transferencia(
            id_transferencia=request.args.get('id_transferencia'),
            tipo=request.args.get('tipo'),
            id_conta_origem=request.args.get('id_conta_origem'),
            id_fatura=request.args.get('id_fatura'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )


@api.route('/entre-contas')
class TransferenciaEntreContas(Resource):
    @api.expect(entre_contas_model, validate=True)
    def post(self):
        """Transfere saldo entre duas contas"""
        parm_dict = request.get_json()

        id_transf = transf_f().transferir_entre_contas(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO,
                {'id_transferencia': id_transf})
        )


@api.route('/pagar-fatura')
class TransferenciaPagarFatura(Resource):
    @api.expect(pagar_fatura_model, validate=True)
    def post(self):
        """Paga uma fatura (baixa o saldo e marca a fatura como paga)"""
        parm_dict = request.get_json()

        id_transf = transf_f().pagar_fatura(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO,
                {'id_transferencia': id_transf})
        )
