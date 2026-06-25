import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiTransferenciaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_transferencia(
            self,
            id_transferencia: int = None,
            tipo: str = None,
            id_conta_origem: int = None,
            id_conta_destino: int = None,
            id_cofre: int = None,
            id_fatura: int = None,
    ) -> dict:
        rotina = 'get_transferencia'

        try:
            query = """
                SELECT * FROM transferencia
                where 1=1
            """

            params = {}

            if id_transferencia:
                query += " and id_transferencia = %(id_transferencia)s"
                params['id_transferencia'] = id_transferencia
            if tipo:
                query += " and tipo = %(tipo)s"
                params['tipo'] = tipo
            if id_conta_origem:
                query += " and id_conta_origem = %(id_conta_origem)s"
                params['id_conta_origem'] = id_conta_origem
            if id_conta_destino:
                query += " and id_conta_destino = %(id_conta_destino)s"
                params['id_conta_destino'] = id_conta_destino
            if id_cofre:
                query += " and id_cofre = %(id_cofre)s"
                params['id_cofre'] = id_cofre
            if id_fatura:
                query += " and id_fatura = %(id_fatura)s"
                params['id_fatura'] = id_fatura

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_transferencia(self, parm_dict: dict):
        rotina = 'insert_transferencia'

        try:
            cmdSql = """
                INSERT INTO transferencia (
                    tipo, valor, data, descricao,
                    id_conta_origem, id_conta_destino, id_cofre, id_fatura
                )
                VALUES (
                    %(tipo)s, %(valor)s, %(data)s, %(descricao)s,
                    %(id_conta_origem)s, %(id_conta_destino)s,
                    %(id_cofre)s, %(id_fatura)s
                )
                RETURNING id_transferencia
            """

            params = {
                "tipo": parm_dict.get("tipo"),
                "valor": parm_dict.get("valor"),
                "data": parm_dict.get("data"),
                "descricao": parm_dict.get("descricao"),
                "id_conta_origem": parm_dict.get("id_conta_origem"),
                "id_conta_destino": parm_dict.get("id_conta_destino"),
                "id_cofre": parm_dict.get("id_cofre"),
                "id_fatura": parm_dict.get("id_fatura"),
            }

            id_transferencia = self.execute_dml_command_parms(cmdSql, params)
            return id_transferencia

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_transferencia(self, id_transferencia: int):
        rotina = 'delete_transferencia'

        try:
            cmdSql = """
                DELETE FROM transferencia
                WHERE id_transferencia = %(id_transferencia)s
            """

            params = {'id_transferencia': id_transferencia}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
