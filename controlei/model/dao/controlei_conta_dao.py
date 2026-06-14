import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiContaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_conta(
            self,
            id_conta: int = None,
            id_usuario: int = None,
    ) -> dict:
        rotina = 'get_conta'

        try:
            # O SALDO é derivado e vive no método único
            query = """
                SELECT
                    c.*,
                    i.dsc_instituicao,
                    i.cor,
                    i.logo_slug,
                    i.tipo AS tipo_instituicao
                FROM conta c
                LEFT JOIN instituicao i
                    ON i.id_instituicao = c.id_instituicao
                where 1=1
            """

            params = {}

            if id_conta:
                query += " and c.id_conta = %(id_conta)s"
                params['id_conta'] = id_conta
            if id_usuario:
                query += " and c.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_conta(self, parm_dict: dict):
        rotina = 'insert_conta'

        try:
            cmdSql = """
                INSERT INTO conta (
                    id_usuario, id_instituicao, apelido, tipo
                )
                VALUES (
                    %(id_usuario)s, %(id_instituicao)s, %(apelido)s, %(tipo)s
                )
                RETURNING id_conta
            """

            params = {
                "id_usuario": parm_dict.get("id_usuario"),
                "id_instituicao": parm_dict.get("id_instituicao"),
                "apelido": parm_dict.get("apelido"),
                "tipo": parm_dict.get("tipo"),
            }

            id_conta = self.execute_dml_command_parms(cmdSql, params)
            return id_conta

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_conta(self, parm_dict: dict):
        rotina = 'update_conta'

        try:
            # id_usuario não muda numa edição de conta.
            cmdSql = """
                UPDATE conta
                SET
                    id_instituicao = %(id_instituicao)s,
                    apelido        = %(apelido)s,
                    tipo           = %(tipo)s
                WHERE id_conta = %(id_conta)s
            """

            params = {
                "id_conta": parm_dict["id_conta"],
                "id_instituicao": parm_dict.get("id_instituicao"),
                "apelido": parm_dict.get("apelido"),
                "tipo": parm_dict.get("tipo"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_conta(
            self,
            id_conta: int,
    ):
        rotina = 'delete_conta'

        try:
            # Cuidado: o schema tem ON DELETE CASCADE — apaga cartões, cofres e
            # lançamentos da conta junto.
            cmdSql = """
                DELETE FROM conta
                WHERE id_conta = %(id_conta)s
            """

            params = {
                'id_conta': id_conta,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
