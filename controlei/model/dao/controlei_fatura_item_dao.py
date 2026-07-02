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
                    id_fatura, id_compra, tipo, descricao, valor, import_ref
                )
                VALUES (
                    %(id_fatura)s, %(id_compra)s, %(tipo)s,
                    %(descricao)s, %(valor)s, %(import_ref)s
                )
                RETURNING id_fatura_item
            """

            params = {
                "id_fatura": parm_dict.get("id_fatura"),
                "id_compra": parm_dict.get("id_compra"),
                "tipo": parm_dict.get("tipo"),
                "descricao": parm_dict.get("descricao"),
                "valor": parm_dict.get("valor"),
                "import_ref": parm_dict.get("import_ref"),
            }

            id_item = self.execute_dml_command_parms(cmdSql, params)
            return id_item

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def existe_import_ref(self, id_cartao: int, import_ref: str) -> bool:
        """True se já existe item de fatura com esse identificador de
        importação (FITID/hash) no cartão — dedup de créditos/estornos."""
        rotina = 'existe_import_ref'

        try:
            cmdSql = """
                SELECT 1
                  FROM fatura_item fi
                  JOIN fatura f ON f.id_fatura = fi.id_fatura
                 WHERE f.id_cartao = %(id_cartao)s
                   AND fi.import_ref = %(import_ref)s
                 LIMIT 1
            """
            params = {"id_cartao": id_cartao, "import_ref": import_ref}
            dataframe = pd.read_sql(
                sql=cmdSql, con=self.get_connection(), params=params)
            resultado = self.convert_dataframe_to_dict(dataframe)
            return len(resultado) > 0

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
