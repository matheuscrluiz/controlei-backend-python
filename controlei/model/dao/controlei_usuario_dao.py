import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiUserDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    # ------------------------------------------------------------------
    # Leitura "segura": NUNCA devolve senha_hash. Filtros opcionais.
    # ------------------------------------------------------------------
    def get_user(self, id_usuario: int = None, email: str = None) -> dict:
        rotina = 'get_user'

        try:
            query = """
                select id_usuario, nome, email, criado_em
                from usuario
                where 1=1
            """

            params = {}

            if id_usuario:
                query += " and id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario
            if email:
                query += " and email = %(email)s"
                params['email'] = email

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # ------------------------------------------------------------------
    # Para autenticação: inclui senha_hash. Usado pelo fluxo de login.
    # ------------------------------------------------------------------
    def get_credenciais_by_email(self, email: str) -> dict:
        rotina = 'get_credenciais_by_email'

        try:
            query = """
                select id_usuario, nome, email, senha_hash
                from usuario
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
                INSERT INTO usuario (nome, email, senha_hash)
                VALUES (%(nome)s, %(email)s, %(senha_hash)s)
                returning id_usuario
            """

            params = {
                "nome": parm_dict.get("nome"),
                "email": parm_dict.get("email"),
                "senha_hash": parm_dict.get("senha_hash")
            }

            id_usuario = self.execute_dml_command_parms(cmdSql, params)
            return id_usuario

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_usuario(self, parm_dict: dict):
        rotina = 'update_usuario'

        try:
            cmdSql = """
                UPDATE usuario
                SET
                    nome  = %(nome)s,
                    email = %(email)s
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": parm_dict['id_usuario'],
                "nome": parm_dict['nome'],
                "email": parm_dict['email']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # Troca de senha isolada: só mexe no hash.
    def update_senha(self, id_usuario: int, senha_hash: str):
        rotina = 'update_senha'

        try:
            cmdSql = """
                UPDATE usuario
                SET senha_hash = %(senha_hash)s
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": id_usuario,
                "senha_hash": senha_hash
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
