import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiReceitaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_income(
            self,
            id_receita: int = None,
            ch_rede: str = None,
            tipo_filtro: str = None,
            mes_inicial: str = None,
            mes_final: str = None,
            ano: str = None,
            data_dia: str = None
    ) -> dict:
        rotina = 'get_income'

        try:
            query = """
                SELECT
                    r.id_receita,
                    r.id_categoria,
                    c.dsc_categoria,
                    u.nome,
                    u.ch_rede,
                    r.dsc_receita,
                    r.valor,
                    r.data_recebimento,
                    r.receita_recorrente,
                    r.origem_receita
                FROM receita r
                join usuario u
                    on r.ch_rede = u.ch_rede
                join categoria c
                    on r.id_categoria = c.id_categoria
                where r.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_receita:
                query += " and id_receita = %(id_receita)s"
                params_oracle['id_receita'] = id_receita

            if tipo_filtro == "MES" and mes_inicial and mes_final:
                query += """
                    AND TO_CHAR(
                    r.data_recebimento, 'MM/YYYY') >= %(mes_inicial)s
                    AND TO_CHAR(
                    r.data_recebimento, 'MM/YYYY') <= %(mes_final)s
                """
                params_oracle["mes_inicial"] = mes_inicial
                params_oracle["mes_final"] = mes_final

            elif tipo_filtro == "ANO" and ano:
                query += """
                    AND TO_CHAR(r.data_recebimento, 'YYYY') = %(ano)s
                """
                params_oracle["ano"] = ano

            elif tipo_filtro == "DIA" and data_dia:
                query += """ AND TO_CHAR(
                r.data_recebimento, 'DD/MM/YYYY') = %(data_dia)s"""
                params_oracle["data_dia"] = data_dia

            print('query: ', query)
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_income(self, parm_dict: dict):
        rotina = 'insert_income'

        try:
            cmdSql = """
                INSERT INTO receita (
                    id_categoria,
                    ch_rede,
                    dsc_receita,
                    valor,
                    data_recebimento,
                    receita_recorrente,
                    origem_receita
                )
                VALUES (
                    %(id_categoria)s,
                    %(ch_rede)s,
                    %(dsc_receita)s,
                    %(valor)s,
                    %(data_recebimento)s,
                    %(receita_recorrente)s,
                    %(origem_receita)s
                )
                RETURNING id_receita
            """

            parms = {
                "id_categoria": parm_dict.get("id_categoria"),
                "ch_rede": parm_dict.get("ch_rede"),
                "dsc_receita": parm_dict.get("dsc_receita"),
                "valor": parm_dict.get("valor"),
                "data_recebimento": parm_dict.get("data_recebimento"),
                "receita_recorrente": parm_dict.get("receita_recorrente"),
                "origem_receita": parm_dict.get("origem_receita"),
            }

            id_receita = self.execute_dml_command_parms(cmdSql, parms)
            return id_receita

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_income(self, parm_dict: dict):
        rotina = 'update_income'

        try:
            cmdSql = """
                UPDATE receita
                SET
                    id_categoria        = %(id_categoria)s,
                    ch_rede             = %(ch_rede)s,
                    dsc_receita         = %(dsc_receita)s,
                    valor               = %(valor)s,
                    data_recebimento    = %(data_recebimento)s,
                    receita_recorrente  = %(receita_recorrente)s,
                    origem_receita      = %(origem_receita)s
                WHERE id_receita = %(id_receita)s
            """

            params = {
                "id_receita": parm_dict["id_receita"],
                "id_categoria": parm_dict["id_categoria"],
                "ch_rede": parm_dict["ch_rede"],
                "dsc_receita": parm_dict.get("dsc_receita"),
                "valor": parm_dict["valor"],
                "data_recebimento": parm_dict["data_recebimento"],
                "receita_recorrente": parm_dict.get("receita_recorrente"),
                "origem_receita": parm_dict.get("origem_receita"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_income(
            self,
            id_receita: int,
            ch_rede: str
    ):
        rotina = 'delete_income'

        try:
            cmdSql = """
                DELETE FROM receita
                WHERE id_receita = %(id_receita)s
                and ch_rede = %(ch_rede)s
            """

            params = {
                'id_receita': id_receita,
                'ch_rede': ch_rede
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
