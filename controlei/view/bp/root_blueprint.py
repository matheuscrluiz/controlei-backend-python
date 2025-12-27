from flask import Blueprint
from flask_restx import Api

from controlei.util.custom_http_messages import (
    custom_http_after_request, custom_http_erros)

from ...util.constants import BLUE_PRINT_BASE_URL
from ..api.area_api import api as area_api
from ..api.controlei_usuario_api import api as controlei_usuario_api
from ..api.controlei_categoria_api import api as controlei_categoria_api
from ..api.controlei_meio_pagamento_api import (
    api as controlei_meio_pagamento_api)
from ..api.controlei_receita_api import api as controlei_receita_api
from ..api.controlei_despesa_api import api as controlei_despesa_api
from ..api.controlei_tipo_categoria_api import (
    api as controlei_tipo_categoria_api)
from ..api.login_api import api as login_api
# ---------------------------->>
# Constants
# ---------------------------->>
BLUE_PRINT_NAME = 'root-bp'
BLUE_PRINT_URL_PREFIX = BLUE_PRINT_BASE_URL
API_VERSION = '1.0'
API_TITLE = 'APIs Controlei'
API_DESCRIPTION = 'API para monitorar minha vida financeira'

# ---------------------------->>
# Registra os Blue Prints
# ---------------------------->>
bp = Blueprint(BLUE_PRINT_NAME, __name__, url_prefix=BLUE_PRINT_URL_PREFIX)

# ----------------------------->>
# Registra Handler After Request
# ----------------------------->>


@bp.after_request
def handler_after_request(self):
    return custom_http_after_request(self)

# ---------------------------->>
# Registra Handler de Http
# ---------------------------->>


# @bp.errorhandler(Exception)
# def handler_custom_error(self):
#     return custom_http_erros(self)
@bp.errorhandler(Exception)
def handler_custom_error(err):
    return custom_http_erros(err)


# ---------------------------->>
# API
# ---------------------------->>


api = Api(bp, version=API_VERSION, base_url=BLUE_PRINT_BASE_URL,
          title=API_TITLE, description=API_DESCRIPTION)

# ---------------------------->>
# Registra as namespaces da API
# ---------------------------->>
api.add_namespace(area_api)
api.add_namespace(controlei_usuario_api)
api.add_namespace(controlei_categoria_api)
api.add_namespace(controlei_meio_pagamento_api)
api.add_namespace(controlei_receita_api)
api.add_namespace(controlei_despesa_api)
api.add_namespace(controlei_tipo_categoria_api)
api.add_namespace(login_api)
# ---------------------------->>
# Inicializa a aplicação
# ---------------------------->>


def init_app(app):
    print('Inicialização Root BluePrint')
    app.register_blueprint(bp)
