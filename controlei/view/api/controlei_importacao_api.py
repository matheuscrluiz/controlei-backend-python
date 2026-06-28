from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from werkzeug.datastructures import FileStorage
from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_importacao_facade import (
    ControleiImportacaoFacade as imp_f
)

# ---------------------------->>
# NameSpace
# ---------------------------->>
api = Namespace('controlei-importacao',
                description='Importação de fatura (OFX)')

# ---------------------------->>
# Parsers
# ---------------------------->>
preview_parser = api.parser()
preview_parser.add_argument(
    'arquivo', location='files', type=FileStorage, required=True,
    help='Arquivo .ofx da fatura')
preview_parser.add_argument(
    'id_cartao', location='form', type=int, required=True,
    help='ID do cartão de destino')

preview_conta_parser = api.parser()
preview_conta_parser.add_argument(
    'arquivo', location='files', type=FileStorage, required=True,
    help='Arquivo .ofx do extrato da conta')
preview_conta_parser.add_argument(
    'id_conta', location='form', type=int, required=True,
    help='ID da conta de destino')

# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('/ofx/preview')
class ImportarOfxPreview(Resource):
    @api.expect(preview_parser)
    def post(self):
        """Lê o OFX e devolve os itens para revisão (não grava nada)"""
        args = preview_parser.parse_args()
        arquivo = args['arquivo']
        id_cartao = args['id_cartao']

        conteudo = arquivo.read()
        itens = imp_f().preview_ofx(conteudo, id_cartao)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, itens)
        )


@api.route('/ofx/confirmar')
class ImportarOfxConfirmar(Resource):
    def post(self):
        """Cria as compras dos itens selecionados (dedup por FITID).
        Body: { id_cartao, itens: [ {fitid, data, descricao, valor,
        id_categoria} ] }"""
        body = request.get_json() or {}
        resultado = imp_f().confirmar(
            body.get('id_cartao'), body.get('itens'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )


@api.route('/ofx/conta/preview')
class ImportarOfxContaPreview(Resource):
    @api.expect(preview_conta_parser)
    def post(self):
        """Lê o OFX de extrato e devolve os itens para revisão (não grava)"""
        args = preview_conta_parser.parse_args()
        conteudo = args['arquivo'].read()
        itens = imp_f().preview_ofx_conta(conteudo, args['id_conta'])

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, itens)
        )


@api.route('/ofx/conta/confirmar')
class ImportarOfxContaConfirmar(Resource):
    def post(self):
        """Cria os lançamentos dos itens selecionados (dedup por FITID).
        Body: { id_conta, itens: [...] }"""
        body = request.get_json() or {}
        resultado = imp_f().confirmar_conta(
            body.get('id_conta'), body.get('itens'))

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )
