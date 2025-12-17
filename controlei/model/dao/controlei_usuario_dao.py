import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiUserDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_user(self, ch_rede: str = None) -> dict:
        rotina = 'get_user'

        try:

            query = """
                select * from usuario
                where 1=1
            """

            params_oracle = {}

            if ch_rede:
                query += " and ch_rede = %(ch_rede)s"
                params_oracle['ch_rede'] = ch_rede

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

    def insert_usuario(self, parm_dict: dict):
        rotina = 'insert_usuario'

        try:

            cmdSql = """
                INSERT INTO usuario (ch_rede, matricula, cpf,
                nome, senha, email)
                VALUES (%(ch_rede)s,%(matricula)s,%(cpf)s,%(nome)s,
                  %(senha)s, %(email)s)
                returning id_usuario
            """

            parms_oracle = {
                "ch_rede": parm_dict.get("ch_rede"),
                "matricula": parm_dict.get("matricula"),
                "cpf": parm_dict.get("cpf"),
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
                SET
                    ch_rede        = %(ch_rede)s,
                    matricula        = %(matricula)s,
                    cpf        = %(cpf)s,
                    nome        = %(nome)s,
                    email       = %(email)s,
                    senha       = %(senha)s,
                    alterado_em = NOW()
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": parm_dict['id_usuario'],
                "ch_rede": parm_dict['ch_rede'],
                "matricula": parm_dict['matricula'],
                "cpf": parm_dict['cpf'],
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
