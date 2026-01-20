from datetime import datetime

import pandas as pd
from dateutil import parser


def printConsoleErro(erro, routine=None):
    if routine:
        formatted_message = f"[{erro}]: {routine}"
    else:
        formatted_message = f"{erro}"
    return formatted_message


def get_dict_retorno_endpoint(
        tip_retorno: str,
        msg_retorno: str,
        dados_retorno: dict) -> dict:

    return {
        'resp_server': {
            'tip_retorno': tip_retorno.lower(),
            'msg_retorno': msg_retorno
        },
        'data_return': dados_retorno
    }


def convert_unique_dic_to_arrayDict(dic_or_df) -> list:
    if isinstance(dic_or_df, pd.DataFrame):
        # Se for um DataFrame pandas, converte para uma lista de dicionários
        return dic_or_df.to_dict(orient='records')
    elif isinstance(dic_or_df, dict):
        # Se for um único dicionário, coloca em uma lista
        return [dic_or_df]
    elif isinstance(dic_or_df, list):
        # Se já for uma lista de dicionários, retorna como está
        return dic_or_df
    else:
        # Se não for nem DataFrame, nem dicionário, retorna uma lista vazia
        return []


# def convert_unique_dic_to_arrayDict(dic: dict) -> list:
#     if not (type(dic) == list):
#         if dic:
#             return [dic]
#         else:
#             return []
#     else:
#         return dic


def convert_to_date(date_str: str) -> datetime.date:
    """
    Converte uma string de data em formato ISO8601 
    ou simples para um objeto `date`.
    """
    try:
        # Caso a string seja o formato ISO8601 com a parte 'Z' ou milissegundos
        if 'T' in date_str and 'Z' in date_str:
            # Remove o 'Z' e a parte de milissegundos
            date_str = date_str.replace('Z', '').split('.')[0]
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").date()
        # Caso tenha apenas data no formato 'YYYY-MM-DD'
        elif len(date_str) == 10:  # Assume o formato 'YYYY-MM-DD'
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        # Caso a string tenha qualquer outro formato
        else:
            # Usa o dateutil.parser para uma maior flexibilidade de formatos
            return parser.isoparse(date_str).date()
    except Exception as e:
        print(f"Erro ao converter a data: {e}")
        raise ValueError(f"Erro ao converter a data: {date_str}")
