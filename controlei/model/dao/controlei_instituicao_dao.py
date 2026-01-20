import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiInstituicaoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_bank(
            self,
            id_instituicao: int = None,

    ) -> dict:
        rotina = 'get_bank'

        try:
            query = """
                SELECT
                    *
                FROM instituicao i
                where 1=1
            """

            params_oracle = {}

            if id_instituicao:
                query += " and i.id_instituicao = %(id_instituicao)s"
                params_oracle['id_instituicao'] = id_instituicao

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_banks(self, parm_dict: dict):
        rotina = 'insert_banks'

        try:
            cmdSql = """
                INSERT INTO instituicao (
                   dsc_instituicao
                )
                VALUES (
                    %(dsc_instituicao)s
                )
                RETURNING id_instituicao
            """

            parms = {
                "dsc_instituicao": parm_dict.get("dsc_instituicao")
            }

            id_instituicao = self.execute_dml_command_parms(cmdSql, parms)
            return id_instituicao

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_banks(self, parm_dict: dict):
        rotina = 'update_banks'

        try:
            cmdSql = """
                UPDATE instituicao
                SET
                    dsc_instituicao        = %(dsc_instituicao)s
                WHERE id_instituicao = %(id_instituicao)s
            """

            params = {
                "id_instituicao": parm_dict["id_instituicao"],
                "dsc_instituicao": parm_dict["dsc_instituicao"]
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_banks(
            self,
            id_instituicao: int,
    ):
        rotina = 'delete_banks'

        try:
            cmdSql = """
                DELETE FROM instituicao
                WHERE id_instituicao = %(id_instituicao)s
            """

            params = {
                'id_instituicao': id_instituicao,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
