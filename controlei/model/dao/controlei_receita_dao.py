import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiReceitaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_income(
            self,
            id_receita: int = None,
            id_usuario: int = None) -> dict:
        rotina = 'get_income'

        try:

            query = """
                SELECT
                    r.id_receita,
                    r.id_categoria,
                    r.id_usuario,
                    u.nome,
                    r.dsc_receita,
                    r.valor,
                    r.data_recebimento,
                    r.receita_recorrente,
                    r.origem_receita
                FROM receita r
                join usuario u
                    on r.id_usuario = u.id_usuario
                where r.id_usuario = %(id_usuario)s
            """

            params_oracle = {"id_usuario": id_usuario}

            if id_receita:
                query += " and id_receita = %(id_receita)s"
                params_oracle['id_receita'] = id_receita

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
                    id_usuario,
                    dsc_receita,
                    valor,
                    data_recebimento,
                    receita_recorrente,
                    origem_receita
                )
                VALUES (
                    %(id_categoria)s,
                    %(id_usuario)s,
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
                "id_usuario": parm_dict.get("id_usuario"),
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
                    id_usuario          = %(id_usuario)s,
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
                "id_usuario": parm_dict["id_usuario"],
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
            id_usuario: int
    ):
        rotina = 'delete_income'

        try:
            cmdSql = """
                DELETE FROM receita
                WHERE id_receita = %(id_receita)s
                and id_usuario = %(id_usuario)s
            """

            params = {
                'id_receita': id_receita,
                'id_usuario': id_usuario
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
