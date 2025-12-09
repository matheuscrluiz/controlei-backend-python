# coding: utf-8
from controlei.util.exceptions import DAOException
from ...util.constants import (
    DATABASE_HOST,
    DATABASE_PASSWORD,
    DATABASE_USERNAME,
    DATABASE_NAME,
    DATABASE_PORT
)
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


class DAOBase:

    def __init__(self):
        """
        Classe base para DAOs usando PostgreSQL.
        """
        self.username = DATABASE_USERNAME
        self.password = DATABASE_PASSWORD
        self.host = DATABASE_HOST
        self.dbname = DATABASE_NAME
        self.port = getattr(globals(), "DATABASE_PORT", 5432)

    # ----------------------------------------------------------------------
    # GET CONNECTION
    # ----------------------------------------------------------------------
    def get_connection(self):
        """
        Retorna uma conexão ativa com o PostgreSQL.
        """
        try:
            if not hasattr(self, "connection") or self.connection is None or self.connection.closed != 0:
                self.connection = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.username,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
            return self.connection
        except Exception as err:
            raise Exception(f"Erro ao conectar ao PostgreSQL: {err}")

    # ----------------------------------------------------------------------
    # UTIL PARA TRANSFORMAR DATAFRAME EM DICT
    # ----------------------------------------------------------------------

    def convert_dataframe_to_dict(self, dataframe):
        """
        Converte o dataframe retornado pelo pandas em uma lista de dicts.
        """
        return dataframe.to_dict(orient="records")

    # ------------------------------------------------------------------

    def database_commit(self):
        self.connection.commit()

    # ------------------------------------------------------------------

    def execute_dml_command_parms(self, sql: str, params: dict):
        """
        Executa INSERT, UPDATE, DELETE com parâmetros (%(campo)s)
        e retorna o valor do RETURNING, se existir.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(sql, params)

        # Se o SQL tiver RETURNING, pegar o ID
        try:
            result = cursor.fetchone()
            if result:
                return result[0]
        except Exception:
            pass  # não tem RETURNING

        return None
