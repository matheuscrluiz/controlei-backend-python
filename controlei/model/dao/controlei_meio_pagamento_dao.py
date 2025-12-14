import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiMeioPagamentoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_meio_pagamento(self, id_meio_pagamento: int = None) -> dict:
        rotina = 'get_meio_pagamento'

        try:

            query = """
                select * from meio_pagamento
                where 1=1
            """

            params_oracle = {}

            if id_meio_pagamento:
                query += " and id_meio_pagamento = %(id_meio_pagamento)s"
                params_oracle['id_meio_pagamento'] = id_meio_pagamento

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_meio_pagamento(self, parm_dict: dict):
        rotina = 'insert_meio_pagamento'

        try:

            cmdSql = """
                INSERT INTO meio_pagamento (dsc_meio_pagamento)
                VALUES (%(dsc_meio_pagamento)s)
                returning id_meio_pagamento
            """

            parms_oracle = {
                "dsc_meio_pagamento": parm_dict.get("dsc_meio_pagamento")
            }

            id_meio_pagamento = self.execute_dml_command_parms(
                cmdSql, parms_oracle)
            return id_meio_pagamento

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_meio_pagamento(self, parm_dict: dict):
        rotina = 'update_meio_pagamento'

        try:
            cmdSql = """
                UPDATE meio_pagamento
                SET dsc_meio_pagamento       = %(dsc_meio_pagamento)s
                WHERE id_meio_pagamento = %(id_meio_pagamento)s
            """

            params = {
                "dsc_meio_pagamento": parm_dict['dsc_meio_pagamento'],
                "id_meio_pagamento": parm_dict['id_meio_pagamento']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_meio_pagamento(self, id_meio_pagamento: int):
        rotina = 'delete_meio_pagamento'

        try:
            cmdSql = """
                DELETE FROM meio_pagamento
                WHERE id_meio_pagamento = %(id_meio_pagamento)s
            """

            params = {'id_meio_pagamento': id_meio_pagamento}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
