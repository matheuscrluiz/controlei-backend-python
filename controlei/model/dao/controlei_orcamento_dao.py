import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiOrcamentoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_orcamento(
            self,
            id_orcamento: int = None,
            id_usuario: int = None,
            id_categoria: int = None):
        """Busca linhas cruas (por id / usuário / categoria).
        Não filtra competência — usado por update/delete/listagens."""
        rotina = 'get_orcamento'

        try:
            query = """
                SELECT o.*, cat.dsc_categoria
                FROM orcamento o
                JOIN categoria cat ON cat.id_categoria = o.id_categoria
                WHERE 1=1
            """

            params = {}

            if id_orcamento:
                query += " and o.id_orcamento = %(id_orcamento)s"
                params['id_orcamento'] = id_orcamento
            if id_usuario:
                query += " and o.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario
            if id_categoria:
                query += " and o.id_categoria = %(id_categoria)s"
                params['id_categoria'] = id_categoria

            query += " ORDER BY cat.dsc_categoria"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_padrao(self, id_usuario: int, id_categoria: int = None):
        """Tetos PADRÃO (competencia IS NULL) do usuário."""
        rotina = 'get_padrao'

        try:
            query = """
                SELECT o.*, cat.dsc_categoria
                FROM orcamento o
                JOIN categoria cat ON cat.id_categoria = o.id_categoria
                WHERE o.id_usuario = %(id_usuario)s
                  AND o.competencia IS NULL
            """
            params = {'id_usuario': id_usuario}
            if id_categoria:
                query += " and o.id_categoria = %(id_categoria)s"
                params['id_categoria'] = id_categoria
            query += " ORDER BY cat.dsc_categoria"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_override(
            self, id_usuario: int, competencia, id_categoria: int = None):
        """Tetos OVERRIDE de um mês específico (competencia = 1º dia)."""
        rotina = 'get_override'

        try:
            query = """
                SELECT o.*, cat.dsc_categoria
                FROM orcamento o
                JOIN categoria cat ON cat.id_categoria = o.id_categoria
                WHERE o.id_usuario = %(id_usuario)s
                  AND o.competencia = %(competencia)s
            """
            params = {'id_usuario': id_usuario, 'competencia': competencia}
            if id_categoria:
                query += " and o.id_categoria = %(id_categoria)s"
                params['id_categoria'] = id_categoria
            query += " ORDER BY cat.dsc_categoria"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_efetivo(self, id_usuario: int, competencia):
        """Teto EFETIVO por categoria no mês: usa o override do mês se
        existir, senão o padrão. Uma linha por categoria."""
        rotina = 'get_efetivo'

        try:
            query = """
                SELECT DISTINCT ON (o.id_categoria)
                       o.id_orcamento, o.id_usuario, o.id_categoria,
                       o.valor_teto, o.competencia, cat.dsc_categoria,
                       (o.competencia IS NOT NULL) AS eh_override
                  FROM orcamento o
                  JOIN categoria cat ON cat.id_categoria = o.id_categoria
                 WHERE o.id_usuario = %(id_usuario)s
                   AND (o.competencia = %(competencia)s
                        OR o.competencia IS NULL)
                 ORDER BY o.id_categoria, o.competencia NULLS LAST
            """
            params = {'id_usuario': id_usuario, 'competencia': competencia}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_orcamento(self, parm_dict: dict):
        rotina = 'insert_orcamento'

        try:
            cmdSql = """
                INSERT INTO orcamento (
                    id_usuario, id_categoria, valor_teto, competencia
                )
                VALUES (
                    %(id_usuario)s, %(id_categoria)s,
                    %(valor_teto)s, %(competencia)s
                )
                RETURNING id_orcamento
            """

            params = {
                "id_usuario": parm_dict.get("id_usuario"),
                "id_categoria": parm_dict.get("id_categoria"),
                "valor_teto": parm_dict.get("valor_teto"),
                "competencia": parm_dict.get("competencia"),
            }

            id_orcamento = self.execute_dml_command_parms(cmdSql, params)
            return id_orcamento

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_orcamento(self, parm_dict: dict):
        rotina = 'update_orcamento'

        try:
            cmdSql = """
                UPDATE orcamento
                SET valor_teto = %(valor_teto)s
                WHERE id_orcamento = %(id_orcamento)s
            """

            params = {
                "id_orcamento": parm_dict['id_orcamento'],
                "valor_teto": parm_dict.get('valor_teto'),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_orcamento(self, id_orcamento: int):
        rotina = 'delete_orcamento'

        try:
            cmdSql = """
                DELETE FROM orcamento
                WHERE id_orcamento = %(id_orcamento)s
            """

            params = {'id_orcamento': id_orcamento}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
