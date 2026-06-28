import json
import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiImportLayoutDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_layout(self, id_usuario: int, assinatura: str):
        """Mapeamento salvo (dict) para a assinatura, ou None."""
        rotina = 'get_layout'

        try:
            cmdSql = """
                SELECT mapeamento FROM import_layout
                 WHERE id_usuario = %(id_usuario)s
                   AND assinatura = %(assinatura)s
                 LIMIT 1
            """
            params = {"id_usuario": id_usuario, "assinatura": assinatura}
            dataframe = pd.read_sql(
                sql=cmdSql, con=self.get_connection(), params=params)
            resultado = self.convert_dataframe_to_dict(dataframe)
            if not resultado:
                return None
            return json.loads(resultado[0]['mapeamento'])

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def upsert_layout(self, id_usuario: int, assinatura: str,
                      mapeamento: dict):
        rotina = 'upsert_layout'

        try:
            cmdSql = """
                INSERT INTO import_layout (id_usuario, assinatura, mapeamento)
                VALUES (%(id_usuario)s, %(assinatura)s, %(mapeamento)s)
                ON CONFLICT (id_usuario, assinatura)
                DO UPDATE SET mapeamento = EXCLUDED.mapeamento,
                              criada_em = now()
                RETURNING id_import_layout
            """
            params = {
                "id_usuario": id_usuario,
                "assinatura": assinatura,
                "mapeamento": json.dumps(mapeamento),
            }
            return self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def resolve_usuario(self, destino: str, id_destino: int):
        """id_usuario dono da conta/cartão de destino."""
        rotina = 'resolve_usuario'

        try:
            if destino == 'cartao':
                cmdSql = """
                    SELECT co.id_usuario AS id_usuario
                    FROM cartao ca
                    JOIN conta co ON co.id_conta = ca.id_conta
                    WHERE ca.id_cartao = %(id)s
                """
            else:
                cmdSql = """
                    SELECT id_usuario FROM conta WHERE id_conta = %(id)s
                """
            params = {"id": id_destino}
            dataframe = pd.read_sql(
                sql=cmdSql, con=self.get_connection(), params=params)
            resultado = self.convert_dataframe_to_dict(dataframe)
            return resultado[0]['id_usuario'] if resultado else None

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
