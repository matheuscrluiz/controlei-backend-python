import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiCategoriaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_category(
            self,
            id_categoria: int = None,
            id_tipo_categoria: int = None,
            id_usuario: int = None):
        rotina = 'get_category'

        try:
            query = """
                select c.*, t.dsc_tipo_categoria
                from categoria c
                join tipo_categoria t
                    on t.id_tipo_categoria = c.id_tipo_categoria
                where 1=1
            """

            params = {}

            if id_categoria:
                query += " and c.id_categoria = %(id_categoria)s"
                params['id_categoria'] = id_categoria
            if id_tipo_categoria:
                query += " and t.id_tipo_categoria = %(id_tipo_categoria)s"
                params['id_tipo_categoria'] = id_tipo_categoria
            if id_usuario:
                query += " and c.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_categoria(self, parm_dict: dict):
        rotina = 'insert_categoria'

        try:
            cmdSql = """
                INSERT INTO categoria (id_usuario, dsc_categoria,
                    id_tipo_categoria)
                VALUES (%(id_usuario)s, %(dsc_categoria)s,
                    %(id_tipo_categoria)s)
                returning id_categoria
            """

            params = {
                "id_usuario": parm_dict.get("id_usuario"),
                "dsc_categoria": parm_dict.get("dsc_categoria"),
                "id_tipo_categoria": parm_dict.get("id_tipo_categoria")
            }

            id_categoria = self.execute_dml_command_parms(cmdSql, params)
            return id_categoria

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_categoria(self, parm_dict: dict):
        rotina = 'update_categoria'

        try:
            cmdSql = """
                UPDATE categoria
                SET
                    dsc_categoria     = %(dsc_categoria)s,
                    id_tipo_categoria = %(id_tipo_categoria)s
                WHERE id_categoria = %(id_categoria)s
            """

            params = {
                "id_categoria": parm_dict['id_categoria'],
                "dsc_categoria": parm_dict.get('dsc_categoria'),
                "id_tipo_categoria": parm_dict.get('id_tipo_categoria')
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_categoria(
            self,
            id_categoria: int):
        rotina = 'delete_categoria'

        try:
            cmdSql = """
                DELETE FROM categoria
                WHERE id_categoria = %(id_categoria)s
            """

            params = {'id_categoria': id_categoria}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
