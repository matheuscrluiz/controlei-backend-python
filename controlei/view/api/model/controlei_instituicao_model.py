from flask_restx import Model, fields, Namespace


def generate_instituicao_model(api: Namespace, type: str) -> Model:
    model = {

        'dsc_instituicao': fields.String(
            required=True,
            description="Descrição da instituição"
        ),


    }

    if type == 'post':
        return api.model(name='post_instituicao_model', model=model)

    model.update({
        'id_instituicao': fields.Integer(
            required=True,
            description="ID da instituição"
        ),
    })

    return api.model(name='put_instituicao_model', model=model)
