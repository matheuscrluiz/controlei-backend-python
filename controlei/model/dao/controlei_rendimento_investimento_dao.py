import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiRendimentoInvestimentoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_investment_yield(
            self,
            id_rendimento: int = None,
            id_investimento: int = None,
            ch_rede: str = None,

    ) -> dict:
        rotina = 'get_investment_yield'

        try:
            query = """
                SELECT
                    i.id_investimento,
                    r.id_rendimento,
                    c.id_categoria,
                    c.dsc_categoria,
                    i.nome_investimento,
                    u.ch_rede,
                    i.id_instituicao,
                    i.valor_inicial,
                    r.mes_referencia,
                    r.valor_rendimento,
                    i.data_inicio,
                    i.data_fim
                FROM investimento_rendimento r
                join investimento i
                    on r.id_investimento = i.id_investimento
                join usuario u
                    on i.ch_rede = u.ch_rede
                join categoria c
                    on i.id_categoria = c.id_categoria
                where u.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_rendimento:
                query += " and r.id_rendimento = %(id_rendimento)s"
                params_oracle['id_rendimento'] = id_rendimento
            if id_investimento:
                query += " and i.id_investimento = %(id_investimento)s"
                params_oracle['id_investimento'] = id_investimento

            query += " order by i.data_inicio asc"
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_investment_yield(self, parm_dict: dict):
        rotina = 'insert_investment_yield'

        try:
            cmdSql = """
                INSERT INTO investimento_rendimento (
                    id_investimento,
                    mes_referencia,
                    valor_rendimento
                )
                VALUES (
                    %(id_investimento)s,
                    %(mes_referencia)s,
                    %(valor_rendimento)s
                )
                RETURNING id_rendimento
            """

            parms = {
                "id_investimento": parm_dict.get("id_investimento"),
                "mes_referencia": parm_dict.get("mes_referencia"),
                "valor_rendimento": parm_dict.get("valor_rendimento"),
            }

            id_rendimento = self.execute_dml_command_parms(cmdSql, parms)
            return id_rendimento

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_investment_yield(self, parm_dict: dict):
        rotina = 'update_investment_yield'

        try:
            cmdSql = """
                UPDATE investimento_rendimento
                SET
                    mes_referencia               = %(mes_referencia)s,
                    valor_rendimento    = %(valor_rendimento)s
                WHERE id_rendimento = %(id_rendimento)s
            """

            params = {
                "id_rendimento": parm_dict["id_rendimento"],
                "mes_referencia": parm_dict["mes_referencia"],
                "valor_rendimento": parm_dict["valor_rendimento"],
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_investment_yield(
            self,
            id_rendimento: int,
    ):
        rotina = 'delete_investment_yield'

        try:
            cmdSql = """
                DELETE FROM investimento_rendimento
                WHERE id_rendimento = %(id_rendimento)s
            """

            params = {
                'id_rendimento': id_rendimento,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
