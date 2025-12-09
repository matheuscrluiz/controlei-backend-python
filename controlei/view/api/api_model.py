from flask_restx import fields

from ...util.constants import NOM_AREA


MODEL_AREA = {

    "nome": fields.String(
        required=True, description=NOM_AREA, min_length=1
    )
}
