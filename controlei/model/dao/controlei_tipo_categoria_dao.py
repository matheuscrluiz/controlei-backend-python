import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiTipoCategoriaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_type_category(self, id_tipo_categoria: int = None) -> dict:
        rotina = 'get_type_category'

        try:

            query = """
                select * from tipo_categoria
                where 1=1
            """

            params_oracle = {}

            if id_tipo_categoria:
                query += " and id_tipo_categoria = %(id_tipo_categoria)s"
                params_oracle['id_tipo_categoria'] = id_tipo_categoria

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_type_category(self, parm_dict: dict):
        rotina = 'insert_type_category'

        try:

            cmdSql = """
                INSERT INTO tipo_categoria (dsc_tipo_categoria,
                codigo_tipo_categoria)
                VALUES (%(dsc_tipo_categoria)s, %(codigo_tipo_categoria)s)
                returning id_tipo_categoria
            """

            parms_oracle = {
                "codigo_tipo_categoria": parm_dict["codigo_tipo_categoria"],
                "dsc_tipo_categoria": parm_dict["dsc_tipo_categoria"]
            }

            id_tipo_categoria = self.execute_dml_command_parms(
                cmdSql, parms_oracle)
            return id_tipo_categoria

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_type_category(self, parm_dict: dict):
        rotina = 'update_type_category'

        try:
            cmdSql = """
                UPDATE tipo_categoria
                SET codigo_tipo_categoria        = %(codigo_tipo_categoria)s,
                    dsc_tipo_categoria       = %(dsc_tipo_categoria)s
                WHERE id_tipo_categoria = %(id_tipo_categoria)s
            """

            params = {
                "id_tipo_categoria": parm_dict['id_tipo_categoria'],
                "codigo_tipo_categoria": parm_dict['codigo_tipo_categoria'],
                "dsc_tipo_categoria": parm_dict['dsc_tipo_categoria']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_type_category(self, id_tipo_categoria: int):
        rotina = 'delete_type_category'

        try:
            cmdSql = """
                DELETE FROM tipo_categoria
                WHERE id_tipo_categoria = %(id_tipo_categoria)s
            """

            params = {'id_tipo_categoria': id_tipo_categoria}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
