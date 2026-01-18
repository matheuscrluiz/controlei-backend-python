import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiMetaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_goals(
            self,
            id_meta: int = None,
            ch_rede: str = None,
    ) -> dict:
        rotina = 'get_goals'

        try:
            query = """
                SELECT
                    m.id_meta,
                    m.prioridade,
                    m.dsc_meta,
                    m.valor_meta,
                    COALESCE(SUM(mm.valor),0) AS valor_atual,
                    (m.valor_meta - COALESCE(SUM(mm.valor),0)) AS falta
                FROM meta m
                LEFT JOIN meta_movimentacao mm
                    ON mm.id_meta = m.id_meta
                WHERE m.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_meta:
                query += " and m.id_meta = %(id_meta)s"
                params_oracle['id_meta'] = id_meta

            query += """
              GROUP BY m.id_meta
              order by m.prioridade
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_goals(self, parm_dict: dict):
        rotina = 'insert_goals'

        try:
            cmdSql = """
                INSERT INTO meta (
                    dsc_meta,
                    ch_rede,
                    prioridade,
                    valor_meta,
                    ativa,
                    criada_em
                )
                VALUES (
                    %(dsc_meta)s,
                    %(ch_rede)s,
                    %(prioridade)s,
                    %(valor_meta)s,
                    %(ativa)s,
                    NOW()
                )
                RETURNING id_meta
            """

            parms = {
                "dsc_meta": parm_dict.get("dsc_meta"),
                "ch_rede": parm_dict.get("ch_rede"),
                "prioridade": parm_dict.get("prioridade"),
                "valor_meta": parm_dict.get("valor_meta"),
                "ativa": parm_dict.get("ativa"),
            }

            id_meta = self.execute_dml_command_parms(cmdSql, parms)
            return id_meta

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_goals(self, parm_dict: dict):
        rotina = 'update_goals'

        try:
            cmdSql = """
                UPDATE meta
                SET
                    dsc_meta        = %(dsc_meta)s,
                    prioridade   = %(prioridade)s,
                    valor_meta         = %(valor_meta)s,
                    ativa         = %(ativa)s
                WHERE id_meta = %(id_meta)s
            """

            params = {
                "id_meta": parm_dict["id_meta"],
                "dsc_meta": parm_dict.get("dsc_meta"),
                "prioridade": parm_dict.get("prioridade"),
                "valor_meta": parm_dict.get("valor_meta"),
                "ativa": parm_dict.get("ativa")
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_goals(
            self,
            id_meta: int,
            ch_rede: str
    ):
        rotina = 'delete_goals'

        try:
            cmdSql = """
                DELETE FROM meta
                WHERE id_meta = %(id_meta)s
                and ch_rede = %(ch_rede)s
            """

            params = {
                'id_meta': id_meta,
                'ch_rede': ch_rede
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def shift_prioridades_down(
        self,
        ch_rede: str,
        inicio: int,
        fim: int
    ):
        rotina = 'shift_prioridades_down'
        try:
            cmdSql = """
                UPDATE meta
                SET prioridade = prioridade + 1
                WHERE ch_rede = %s
                AND prioridade >= %s
                AND prioridade <= %s
            """

            params = (ch_rede, inicio, fim)

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def shift_prioridades_up(
        self,
        ch_rede: str,
        inicio: int,
        fim: int
    ):
        rotina = 'shift_prioridades_up'
        try:
            cmdSql = """
                UPDATE meta
                SET prioridade = prioridade - 1
                WHERE ch_rede = %s
                AND prioridade >= %s
                AND prioridade <= %s
            """
            params = (ch_rede, inicio, fim)

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_monthly_balance_report(self, ch_rede: str) -> dict:
        rotina = 'get_monthly_balance_report'

        try:
            query = """
            WITH saldo_mensal AS (
                SELECT
                    date_trunc('month', mov.data) AS mes,
                    SUM(mov.valor) AS saldo
                FROM (
                    -- Receitas
                    SELECT
                        data_recebimento AS data,
                        valor
                    FROM receita
                    WHERE ch_rede = %(ch_rede)s

                    UNION ALL

                    -- Despesas
                    SELECT
                        data_despesa AS data,
                        -valor_total
                    FROM despesa
                    WHERE ch_rede = %(ch_rede)s
                ) mov
                GROUP BY mes
            ),

            aporte_mensal AS (
                SELECT
                    date_trunc('month', data_movimentacao) AS mes,
                    SUM(valor) AS aportado
                FROM meta_movimentacao
                GROUP BY mes
            )

            SELECT
                s.mes,
                s.saldo,
                COALESCE(a.aportado, 0) AS aportado,
                (s.saldo - COALESCE(a.aportado, 0)) AS disponivel
            FROM saldo_mensal s
            LEFT JOIN aporte_mensal a ON a.mes = s.mes
            ORDER BY s.mes desc;
            """

            params_oracle = {"ch_rede": ch_rede}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
