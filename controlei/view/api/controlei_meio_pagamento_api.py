from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from .model.controlei_meio_pagamento_model import generate_meio_pagamento_model
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_meio_pagamento_facade import (
    ControleiMeioPagamentoFacade as meio_f
)
# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('controlei-meio-pagemento',
                description='Tabela de meio de pagamento')


# ---------------------------->>
# Model
# ---------------------------->>
put_meio_pagamento_model = generate_meio_pagamento_model(api, "put")
post_meio_pagamento_model = generate_meio_pagamento_model(api, "post")


model_get_payment_method = api.parser().add_argument(
    name='id_meio_pagamento',
    type=int,
    help="ID do meio de pagamento"
)

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('')
class ControleiMeioPagamento(Resource):
    @api.expect(model_get_payment_method, validate=True)
    def get(self):
        """Obtém uma ou todos os meios de pagamento"""
        id_meio_pagamento = request.args.get('id_meio_pagamento')
        result = meio_f().obter_meio_pagamento(id_meio_pagamento)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, result)
        )

    @api.expect(post_meio_pagamento_model, validate=True)
    def post(self):
        """Cria um novo meio de pagamento"""
        parm_dict = request.get_json()

        id_meio_pagamento = meio_f().criar_meio_pagamento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                {'id_meio_pagamento': id_meio_pagamento})
        )

    @api.expect(put_meio_pagamento_model, validate=True)
    def put(self):
        """Atualiza um meio de pagamento existente"""
        parm_dict = request.get_json()

        meio_f().atualizar_meio_pagamento(parm_dict)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS,
                MSG_SUCESSO,
                None)
        )
