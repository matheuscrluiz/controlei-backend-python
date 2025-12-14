import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiUserDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_user(self, nome: str = None) -> dict:
        rotina = 'get_user'

        try:

            query = """
                select * from usuario
                where 1=1
            """

            params_oracle = {}

            if nome:
                query += " and nome = %(nome)s"
                params_oracle['nome'] = nome

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_user_by_id(self, id_usuario: int) -> dict:
        rotina = 'get_user_by_id'

        try:
            query = """
                select * from usuario
                where id_usuario = %(id_usuario)s
            """

            params = {'id_usuario': id_usuario}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_user_by_email(self, email: str) -> dict:
        rotina = 'get_user_by_email'

        try:
            query = """
                select * from usuario
                where email = %(email)s
            """

            params = {'email': email}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_usuario(self, parm_dict: dict):
        rotina = 'insert_usuario'

        try:

            cmdSql = """
                INSERT INTO usuario (nome, senha, email)
                VALUES (%(nome)s, %(senha)s, %(email)s)
                returning id_usuario
            """

            parms_oracle = {
                "nome": parm_dict.get("nome"),
                "senha": parm_dict.get("senha"),
                "email": parm_dict.get("email")
            }

            id_usuario = self.execute_dml_command_parms(cmdSql, parms_oracle)
            return id_usuario

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_usuario(self, parm_dict: dict):
        rotina = 'update_usuario'

        try:
            cmdSql = """
                UPDATE usuario
                SET nome        = %(nome)s,
                    email       = %(email)s,
                    senha       = %(senha)s,
                    alterado_em = NOW()
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": parm_dict['id_usuario'],
                "nome": parm_dict['nome'],
                "senha": parm_dict['senha'],
                "email": parm_dict['email']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_usuario(self, id_usuario: int):
        rotina = 'delete_usuario'

        try:
            cmdSql = """
                DELETE FROM usuario
                WHERE id_usuario = %(id_usuario)s
            """

            params = {'id_usuario': id_usuario}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
