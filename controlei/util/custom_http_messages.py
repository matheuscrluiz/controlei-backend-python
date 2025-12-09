# coding: utf-8
import json

from flask import jsonify
from werkzeug.exceptions import BadRequest, HTTPException

from .constants import (DB_INDISPONIVEL, HTTP_STATUS_CODE_BAD_REQUEST,
                        HTTP_STATUS_CODE_INTERNAL_SERVER_ERRO,
                        TIP_RETORNO_AVISO, TIP_RETORNO_ERROR)
from controlei.util.exceptions import FacadeException
from .util import get_dict_retorno_endpoint


def custom_http_erros(err):
    if isinstance(err, BadRequest):
        error_code = err.code
        return {}, error_code

    if isinstance(err, HTTPException):
        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_AVISO,
                str(err), None)
        ), HTTP_STATUS_CODE_BAD_REQUEST

    if isinstance(err, FacadeException):
        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_ERROR,
                str(err), None)
        ), HTTP_STATUS_CODE_BAD_REQUEST

    elif isinstance(err, Exception):

        if 'ORA-12545' in str(err):
            return jsonify(
                get_dict_retorno_endpoint(
                    TIP_RETORNO_ERROR,
                    DB_INDISPONIVEL, None)
            ), HTTP_STATUS_CODE_INTERNAL_SERVER_ERRO

        elif 'ORA-' in str(err):
            erro = str(err)
            oracleError = erro[erro.index('ORA-'):]
            return jsonify(
                get_dict_retorno_endpoint(
                    TIP_RETORNO_ERROR,
                    oracleError, None)
            ), HTTP_STATUS_CODE_BAD_REQUEST

        else:
            return jsonify(
                get_dict_retorno_endpoint(
                    TIP_RETORNO_ERROR,
                    str(err), None)
            ), HTTP_STATUS_CODE_BAD_REQUEST


def translate_request_data(message: str) -> str:

    message = message.replace("'' ", '')

    if message == 'Input payload validation failed':
        return 'A validação dos campos da API falhou!'

    elif "is not of type 'integer'" in message:
        return message.replace("is not of type 'integer'",
                               "Não é do tipo 'inteiro'.")
    elif 'is too short' in message:
        translate = (
            'É uma informação obrigatória e não foi enviada ou possui '
            'tamanho inferior ao mínimo possível.'
        )
        return message.replace('is too short', translate)
    else:
        return message


def custom_http_after_request(response):
    rd = response.get_data()
    if rd is not None:
        if 'json' in response.content_type:
            response_data = json.loads(rd)
            if 'errors' in response_data:
                dados_retorno = response_data['errors']
                for key, value in dados_retorno.items():
                    dados_retorno[key] = translate_request_data(value)
                msg_retorno = translate_request_data(response_data['message'])
                new_response_data = get_dict_retorno_endpoint(
                    TIP_RETORNO_ERROR,
                    msg_retorno,
                    dados_retorno
                )
                response.set_data(json.dumps(new_response_data))
                response.headers.add('Content-Type', 'application/json')
    return response
