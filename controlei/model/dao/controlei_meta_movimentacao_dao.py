import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiMetaMovimentacaoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_movimentacoes(
            self,
            ch_rede: str,
            id_movimentacao: int = None,
            id_meta: int = None,

    ) -> dict:
        rotina = 'get_movimentacoes'

        try:
            query = """
                SELECT
                    mm.id_movimentacao,
                    mm.id_meta,
                    mm.valor,
                    mm.data_movimentacao,
                    mm.origem,
                    m.ch_rede
                FROM meta_movimentacao mm
                join meta m
                    on mm.id_meta = m.id_meta
                WHERE m.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_movimentacao:
                query += " AND id_movimentacao = %(id_movimentacao)s"
                params_oracle['id_movimentacao'] = id_movimentacao

            if id_meta:
                query += " AND id_meta = %(id_meta)s"
                params_oracle['id_meta'] = id_meta

            query += " ORDER BY data_movimentacao DESC"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_movimentacao(self, parm_dict: dict):
        rotina = 'insert_movimentacao'

        try:
            cmdSql = """
                INSERT INTO meta_movimentacao (
                    id_meta,
                    valor,
                    data_movimentacao,
                    origem
                )
                VALUES (
                    %(id_meta)s,
                    %(valor)s,
                    %(data_movimentacao)s,
                    %(origem)s
                )
                RETURNING id_movimentacao
            """

            parms = {
                "id_meta": parm_dict.get("id_meta"),
                "valor": parm_dict.get("valor"),
                "data_movimentacao": parm_dict.get("data_movimentacao"),
                "origem": parm_dict.get("origem"),
            }

            id_movimentacao = self.execute_dml_command_parms(cmdSql, parms)
            return id_movimentacao

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_movimentacao(self, parm_dict: dict):
        rotina = 'update_movimentacao'

        try:
            cmdSql = """
                UPDATE meta_movimentacao
                SET
                    valor = %(valor)s,
                    data_movimentacao = %(data_movimentacao)s,
                    origem = %(origem)s
                WHERE id_movimentacao = %(id_movimentacao)s
            """

            params = {
                "id_movimentacao": parm_dict["id_movimentacao"],
                "valor": parm_dict.get("valor"),
                "data_movimentacao": parm_dict.get("data_movimentacao"),
                "origem": parm_dict.get("origem")
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_movimentacao(
            self,
            id_movimentacao: int
    ):
        rotina = 'delete_movimentacao'

        try:
            cmdSql = """
                DELETE FROM meta_movimentacao
                WHERE id_movimentacao = %(id_movimentacao)s
            """

            params = {
                'id_movimentacao': id_movimentacao
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
