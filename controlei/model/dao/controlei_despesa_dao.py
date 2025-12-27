import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiDespesaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_expenses(
            self,
            id_despesa: int = None,
            ch_rede: str = None,
            tipo_filtro: str = None,
            mes_inicial: str = None,
            mes_final: str = None,
            ano: str = None,
            data_dia: str = None
    ) -> dict:
        rotina = 'get_expenses'

        try:
            query = """
                SELECT
                    d.id_despesa,
                    d.id_categoria,
                    c.dsc_categoria,
                    m.dsc_meio_pagamento,
                    m.id_meio_pagamento,
                    u.nome,
                    u.ch_rede,
                    d.dsc_despesa,
                    d.valor_total,
                    d.data_despesa,
                    d.despesa_recorrente,
                    d.parcelada,
                    d.pago
                FROM despesa d
                join usuario u
                    on d.ch_rede = u.ch_rede
                join categoria c
                    on d.id_categoria = c.id_categoria
                join meio_pagamento m
                    on d.id_meio_pagamento = m.id_meio_pagamento
                where d.ch_rede = %(ch_rede)s
            """

            params_oracle = {"ch_rede": ch_rede}

            if id_despesa:
                query += " and id_despesa = %(id_despesa)s"
                params_oracle['id_despesa'] = id_despesa

            if tipo_filtro == "MES" and mes_inicial and mes_final:
                query += """
                    AND TO_CHAR(
                    d.data_despesa, 'MM/YYYY') >= %(mes_inicial)s
                    AND TO_CHAR(
                    d.data_despesa, 'MM/YYYY') <= %(mes_final)s
                """
                params_oracle["mes_inicial"] = mes_inicial
                params_oracle["mes_final"] = mes_final

            elif tipo_filtro == "ANO" and ano:
                query += """
                    AND TO_CHAR(d.data_despesa, 'YYYY') = %(ano)s
                """
                params_oracle["ano"] = ano

            elif tipo_filtro == "DIA" and data_dia:
                query += """ AND TO_CHAR(
                d.data_despesa, 'DD/MM/YYYY') = %(data_dia)s"""
                params_oracle["data_dia"] = data_dia

            query += " order by d.data_despesa asc"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_expense(self, parm_dict: dict):
        rotina = 'insert_expense'

        try:
            cmdSql = """
                INSERT INTO despesa (
                    id_categoria,
                    id_meio_pagamento,
                    ch_rede,
                    dsc_despesa,
                    valor_total,
                    data_despesa,
                    despesa_recorrente,
                    parcelada,
                    pago
                )
                VALUES (
                    %(id_categoria)s,
                    %(id_meio_pagamento)s,
                    %(ch_rede)s,
                    %(dsc_despesa)s,
                    %(valor_total)s,
                    %(data_despesa)s,
                    %(despesa_recorrente)s,
                    %(parcelada)s,
                    %(pago)s
                )
                RETURNING id_despesa
            """

            parms = {
                "id_categoria": parm_dict.get("id_categoria"),
                "id_meio_pagamento": parm_dict.get("id_meio_pagamento"),
                "ch_rede": parm_dict.get("ch_rede"),
                "dsc_despesa": parm_dict.get("dsc_despesa"),
                "valor_total": parm_dict.get("valor_total"),
                "data_despesa": parm_dict.get("data_despesa"),
                "despesa_recorrente": parm_dict.get("despesa_recorrente"),
                "parcelada": parm_dict.get("parcelada"),
                "pago": parm_dict.get("pago"),
            }

            id_despesa = self.execute_dml_command_parms(cmdSql, parms)
            return id_despesa

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_expense(self, parm_dict: dict):
        rotina = 'update_expense'

        try:
            cmdSql = """
                UPDATE despesa
                SET
                    id_categoria        = %(id_categoria)s,
                    id_meio_pagamento   = %(id_meio_pagamento)s,
                    dsc_despesa         = %(dsc_despesa)s,
                    valor_total         = %(valor_total)s,
                    data_despesa        = %(data_despesa)s,
                    despesa_recorrente  = %(despesa_recorrente)s,
                    parcelada           = %(parcelada)s,
                    pago                = %(pago)s
                WHERE id_despesa = %(id_despesa)s
            """

            params = {
                "id_despesa": parm_dict["id_despesa"],
                "id_categoria": parm_dict.get("id_categoria"),
                "id_meio_pagamento": parm_dict.get("id_meio_pagamento"),
                "dsc_despesa": parm_dict.get("dsc_despesa"),
                "valor_total": parm_dict.get("valor_total"),
                "data_despesa": parm_dict.get("data_despesa"),
                "despesa_recorrente": parm_dict.get("despesa_recorrente"),
                "parcelada": parm_dict.get("parcelada"),
                "pago": parm_dict.get("pago"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_expense(
            self,
            id_despesa: int,
            ch_rede: str
    ):
        rotina = 'delete_expense'

        try:
            cmdSql = """
                DELETE FROM despesa
                WHERE id_despesa = %(id_despesa)s
                and ch_rede = %(ch_rede)s
            """

            params = {
                'id_despesa': id_despesa,
                'ch_rede': ch_rede
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
