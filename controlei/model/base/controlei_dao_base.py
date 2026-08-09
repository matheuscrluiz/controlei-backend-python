# coding: utf-8
import math
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class DAOBase:

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_HOST")
        self.dbname = os.getenv("DATABASE_NAME")
        self.port = os.getenv("DATABASE_PORT", 5432)

    def get_connection(self):
        try:
            if not hasattr(self, "connection") or self.connection is None or self.connection.closed != 0:
                if self.database_url:
                    # PRODUÇÃO (Render + Neon)
                    self.connection = psycopg2.connect(
                        self.database_url,
                        sslmode="require"
                    )
                else:
                    # LOCAL / LEGADO
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
                df[col] = df[col].astype(object).where(pd.notna(df[col]), None)
                df[col] = df[col].apply(
                    lambda x: x.isoformat() if x is not None else None)

        records = df.to_dict(orient="records")

        # sweep final: NaN/Inf remanescente (inclusive object misto) -> None
        for row in records:
            for k, v in row.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    row[k] = None
        return records

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
