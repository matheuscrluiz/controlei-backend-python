import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiCategoriaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_category(
            self,
            id_categoria: int = None,
            id_tipo_categoria: int = None):
        rotina = 'get_category'

        try:

            query = """
                select c.*, t.* from categoria c
                join tipo_categoria t
                    on t.id_tipo_categoria = c.id_tipo_categoria
                where 1=1
            """

            params_oracle = {}

            if id_categoria:
                query += " and c.id_categoria = %(id_categoria)s"
                params_oracle['id_categoria'] = id_categoria
            if id_tipo_categoria:
                query += " and t.id_tipo_categoria = %(id_tipo_categoria)s"
                params_oracle['id_tipo_categoria'] = id_tipo_categoria

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_categoria(self, parm_dict: dict):
        rotina = 'insert_categoria'

        try:

            cmdSql = """
                INSERT INTO categoria (dsc_categoria, id_tipo_categoria)
                VALUES (%(dsc_categoria)s, %(id_tipo_categoria)s)
                returning id_categoria
            """

            parms_oracle = {
                "dsc_categoria": parm_dict.get("dsc_categoria"),
                "id_tipo_categoria": parm_dict.get("id_tipo_categoria")
            }

            id_categoria = self.execute_dml_command_parms(cmdSql, parms_oracle)
            return id_categoria

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_categoria(self, parm_dict: dict):
        rotina = 'update_categoria'

        try:
            cmdSql = """
                UPDATE categoria
                SET
                    dsc_categoria       = %(dsc_categoria)s
                WHERE id_categoria = %(id_categoria)s
            """

            params = {
                "id_categoria": parm_dict['id_categoria'],
                "dsc_categoria": parm_dict['dsc_categoria']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_categoria(
            self,
            id_categoria: int,
            id_tipo_categoria: int):
        rotina = 'delete_categoria'

        try:
            cmdSql = """
                DELETE FROM categoria
                WHERE id_categoria = %(id_categoria)s
                and id_tipo_categoria = %(id_tipo_categoria)s
            """

            params = {'id_categoria': id_categoria,
                      'id_tipo_categoria': id_tipo_categoria}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
