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
import pandas as pd
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
        df = dataframe.copy()

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # 1️⃣ força para object
                df[col] = df[col].astype(object)

                # 2️⃣ NaT -> None
                df[col] = df[col].where(pd.notna(df[col]), None)

                # 3️⃣ datetime -> ISO string
                df[col] = df[col].apply(
                    lambda x: x.isoformat() if x is not None else None
                )
            else:
                # outras colunas
                df[col] = df[col].where(pd.notnull(df[col]), None)

        return df.to_dict(orient="records")

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
