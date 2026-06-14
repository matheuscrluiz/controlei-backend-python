import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiFaturaItemDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_fatura_item(
            self,
            id_fatura_item: int = None,
            id_fatura: int = None,
            id_compra: int = None,
            tipo: str = None,
    ) -> dict:
        rotina = 'get_fatura_item'

        try:
            query = """
                SELECT *
                FROM fatura_item
                where 1=1
            """

            params = {}

            if id_fatura_item:
                query += " and id_fatura_item = %(id_fatura_item)s"
                params['id_fatura_item'] = id_fatura_item
            if id_fatura:
                query += " and id_fatura = %(id_fatura)s"
                params['id_fatura'] = id_fatura
            if id_compra:
                query += " and id_compra = %(id_compra)s"
                params['id_compra'] = id_compra
            if tipo:
                query += " and tipo = %(tipo)s"
                params['tipo'] = tipo

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_fatura_item(self, parm_dict: dict):
        rotina = 'insert_fatura_item'

        try:
            cmdSql = """
                INSERT INTO fatura_item (
                    id_fatura, id_compra, tipo, descricao, valor
                )
                VALUES (
                    %(id_fatura)s, %(id_compra)s, %(tipo)s,
                    %(descricao)s, %(valor)s
                )
                RETURNING id_fatura_item
            """

            params = {
                "id_fatura": parm_dict.get("id_fatura"),
                "id_compra": parm_dict.get("id_compra"),
                "tipo": parm_dict.get("tipo"),
                "descricao": parm_dict.get("descricao"),
                "valor": parm_dict.get("valor"),
            }

            id_item = self.execute_dml_command_parms(cmdSql, params)
            return id_item

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_fatura_item(self, id_fatura_item: int):
        rotina = 'delete_fatura_item'

        try:
            cmdSql = """
                DELETE FROM fatura_item
                WHERE id_fatura_item = %(id_fatura_item)s
            """

            params = {'id_fatura_item': id_fatura_item}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
