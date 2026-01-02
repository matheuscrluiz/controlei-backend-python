import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiAporteInvestimentoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_investment_injection(
            self,
            id_aporte: int = None,
            ch_rede: str = None,

    ) -> dict:
        rotina = 'get_investment_injection'

        try:
            query = """
                SELECT
                    i.id_investimento,
                    a.id_aporte,
                    c.id_categoria,
                    c.dsc_categoria,
                    i.nome_investimento,
                    u.ch_rede,
                    i.id_instituicao,
                    i.valor_inicial,
                    a.valor_aporte,
                    a.data_aporte,
                    i.data_inicio,
                    i.data_fim
                FROM investimento_aporte a
                join investimento i
                    on a.id_investimento = i.id_investimento
                join usuario u
                    on i.ch_rede = u.ch_rede
                join categoria c
                    on i.id_categoria = c.id_categoria
                where u.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_aporte:
                query += " and id_aporte = %(id_aporte)s"
                params_oracle['id_aporte'] = id_aporte

            query += " order by i.data_inicio asc"
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_investment_injection(self, parm_dict: dict):
        rotina = 'insert_investment_injection'

        try:
            cmdSql = """
                INSERT INTO investimento_aporte (
                    id_investimento,
                    valor_aporte,
                    data_aporte
                )
                VALUES (
                    %(id_investimento)s,
                    %(valor_aporte)s,
                    %(data_aporte)s
                )
                RETURNING id_aporte
            """

            parms = {
                "id_investimento": parm_dict.get("id_investimento"),
                "valor_aporte": parm_dict.get("valor_aporte"),
                "data_aporte": parm_dict.get("data_aporte"),
            }

            id_aporte = self.execute_dml_command_parms(cmdSql, parms)
            return id_aporte

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_investment_injection(self, parm_dict: dict):
        rotina = 'update_investment_injection'

        try:
            cmdSql = """
                UPDATE investimento_aporte
                SET
                    valor_aporte               = %(valor_aporte)s,
                    data_aporte    = %(data_aporte)s
                WHERE id_aporte = %(id_aporte)s
            """

            params = {
                "id_aporte": parm_dict["id_aporte"],
                "valor_aporte": parm_dict["valor_aporte"],
                "data_aporte": parm_dict["data_aporte"],
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_investment_injection(
            self,
            id_aporte: int,
    ):
        rotina = 'delete_investment_injection'

        try:
            cmdSql = """
                DELETE FROM investimento_aporte
                WHERE id_aporte = %(id_aporte)s
            """

            params = {
                'id_aporte': id_aporte,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
