from flask import jsonify, request
import json
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


# ---------------------------->>
# CSV (fatura ou extrato) — destino por 'destino' + 'id_destino'
# ---------------------------->>
csv_inspecionar_parser = api.parser()
csv_inspecionar_parser.add_argument(
    'arquivo', location='files', type=FileStorage, required=True,
    help='Arquivo .csv')
csv_inspecionar_parser.add_argument(
    'destino', location='form', type=str, required=True,
    help="'cartao' ou 'conta'")
csv_inspecionar_parser.add_argument(
    'id_destino', location='form', type=int, required=True,
    help='ID do cartão ou da conta')

csv_preview_parser = api.parser()
csv_preview_parser.add_argument(
    'arquivo', location='files', type=FileStorage, required=True,
    help='Arquivo .csv')
csv_preview_parser.add_argument(
    'destino', location='form', type=str, required=True)
csv_preview_parser.add_argument(
    'id_destino', location='form', type=int, required=True)
csv_preview_parser.add_argument(
    'mapeamento', location='form', type=str, required=True,
    help='JSON {data, valor, descricao, inverter_sinal}')
csv_preview_parser.add_argument(
    'salvar', location='form', type=str, required=False, default='true')


@api.route('/csv/inspecionar')
class ImportarCsvInspecionar(Resource):
    @api.expect(csv_inspecionar_parser)
    def post(self):
        """Lê o CSV: devolve preview (se layout salvo) ou palpite de mapa"""
        args = csv_inspecionar_parser.parse_args()
        conteudo = args['arquivo'].read()
        resultado = imp_f().inspecionar_csv(
            conteudo, args['destino'], args['id_destino'])

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )


@api.route('/csv/preview')
class ImportarCsvPreview(Resource):
    @api.expect(csv_preview_parser)
    def post(self):
        """Aplica o mapeamento (e memoriza o layout) -> preview"""
        args = csv_preview_parser.parse_args()
        conteudo = args['arquivo'].read()
        mapeamento = json.loads(args['mapeamento'])
        salvar = str(args.get('salvar', 'true')).lower() != 'false'
        resultado = imp_f().preview_csv(
            conteudo, args['destino'], args['id_destino'], mapeamento, salvar)

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )


# ---------------------------->>
# PDF (fatura ou extrato)
# ---------------------------->>
pdf_preview_parser = api.parser()
pdf_preview_parser.add_argument(
    'arquivo', location='files', type=FileStorage, required=True,
    help='Arquivo .pdf')
pdf_preview_parser.add_argument(
    'destino', location='form', type=str, required=True,
    help="'cartao' ou 'conta'")
pdf_preview_parser.add_argument(
    'id_destino', location='form', type=int, required=True,
    help='ID do cartão ou da conta')


@api.route('/pdf/preview')
class ImportarPdfPreview(Resource):
    @api.expect(pdf_preview_parser)
    def post(self):
        """Extrai transações do PDF e devolve o preview para revisão"""
        args = pdf_preview_parser.parse_args()
        conteudo = args['arquivo'].read()
        resultado = imp_f().preview_pdf(
            conteudo, args['destino'], args['id_destino'])

        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, resultado)
        )
