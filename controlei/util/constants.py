# coding: utf-8
import os
from .exceptions import InvalidFieldException, NotFoundException

# --------------------------------------------------->>>
# CONFIGURAÇÃO - Variáveis de Ambiente
# --------------------------------------------------->>>
# Flask Environment
FLASK_ENV = os.environ.get("FLASK_ENV")

# Database config
DATABASE_HOST = os.environ.get("DB_HOST")
DATABASE_USERNAME = os.environ.get("DB_USERNAME")
DATABASE_PASSWORD = os.environ.get("DB_PASSWORD")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
DATABASE_PORT = os.environ.get("DATABASE_PORT")

REQUIRED_ENV_VARS = {
    'FLASK_ENV': FLASK_ENV,
    'DATABASE_HOST': DATABASE_HOST,
    'DATABASE_USERNAME': DATABASE_USERNAME,
    'DATABASE_PASSWORD': DATABASE_PASSWORD
}

for var_env in REQUIRED_ENV_VARS.keys():
    if REQUIRED_ENV_VARS.get(var_env) is None:
        raise NotFoundException(f'{var_env} não localizada no ambiente!')

if FLASK_ENV not in ('development', 'testing', 'production'):
    raise InvalidFieldException(
        'Ambiente inválido. Inicialização interrompida!'
    )

print('FLASK_ENV: ', FLASK_ENV)
print('DATABASE_HOST: ', DATABASE_HOST)
print('DATABASE_USERNAME: ', DATABASE_USERNAME)
print('DATABASE_PASSWORD: ', '******')

# --------------------------------------------------->>>
# Caminho Base dos BluePrints
# --------------------------------------------------->>>
BLUE_PRINT_BASE_URL = '/controlei/api'

# --------------------------------------------------->>>
# Root APP
# --------------------------------------------------->>>
HTTP_STATUS_CODE_CREATED = 201
HTTP_STATUS_CODE_BAD_REQUEST = 400
HTTP_STATUS_CODE_INTERNAL_SERVER_ERRO = 500

# ---------------------------------------------------------------------------------------------->>>
# Mensagens Padrão do Sistema
# ---------------------------------------------------------------------------------------------->>>
MSG_PARM_EXEC_NAO_INFOR = (
    'Os parâmetros de execução não foram informados!'
    ' Verifique a documentação do produto'
)
TIP_RETORNO_SUCESS = "SUCCESS"
TIP_RETORNO_AVISO = "WARN"
TIP_RETORNO_ERROR = "ERROR"
MSG_SUCESSO = "Operação Realizada com sucesso!"
OBJETO_EXISTENTE = "O objeto que você tentando cadastrar ja existe!"
OBJETO_EXCLUIDO = "Objeto não foi localizado!"
DB_INDISPONIVEL = "Banco de Dados indisponível. Entre em contato com a TI!"

# ---------------------------------------------------------------------------------------------->>>
# Json retorno
# ---------------------------------------------------------------------------------------------->>>
JSON_RETORNO_SUCESSO = {'message': 'Operação Realizada com sucesso!'}

# ---------------------------------------------------------------------------------------------->>>
# Constants Models
# ---------------------------------------------------------------------------------------------->>>
CLEAN_NUMBER = -1

# ---------------------------------------------------------------------------------------------->>>
# Descriptions Models
# ---------------------------------------------------------------------------------------------->>>
PER_AREA_ID = "ID tabela bi_dm_per_area"
NOM_AREA = "Nome área"
