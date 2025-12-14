from flask_restx import Model, fields, Namespace


def generate_meio_pagamento_model(api: Namespace, type: str) -> Model:
    model = {
        'dsc_meio_pagamento': fields.String(
            required=True,
            description="Dsc. do meio de pagamento"
        ),
    }

    if type == 'post':
        return api.model(name='post_meio_pagamento_model', model=model)

    model.update({
        'id_meio_pagamento': fields.Integer(
            required=True,
            description="ID do meio de pagamento"
        ),

    })
    return api.model(name='put_meio_pagamento_model', model=model)
