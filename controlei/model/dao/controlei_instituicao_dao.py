import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiInstituicaoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_bank(
            self,
            id_instituicao: int = None,

    ) -> dict:
        rotina = 'get_bank'

        try:
            query = """
                SELECT
                    *
                FROM instituicao i
                where 1=1
            """

            params_oracle = {}

            if id_instituicao:
                query += " and i.id_instituicao = %(id_instituicao)s"
                params_oracle['id_instituicao'] = id_instituicao

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_investment(self, parm_dict: dict):
        rotina = 'insert_investment'

        try:
            cmdSql = """
                INSERT INTO investimento (
                    id_categoria,
                    ch_rede,
                    nome_investimento,
                    valor_inicial,
                    data_inicio,
                    data_fim,
                    id_instituicao
                )
                VALUES (
                    %(id_categoria)s,
                    %(ch_rede)s,
                    %(nome_investimento)s,
                    %(valor_inicial)s,
                    %(data_inicio)s,
                    %(data_fim)s,
                    %(id_instituicao)s
                )
                RETURNING id_investimento
            """

            parms = {
                "id_categoria": parm_dict.get("id_categoria"),
                "ch_rede": parm_dict.get("ch_rede"),
                "nome_investimento": parm_dict.get("nome_investimento"),
                "valor_inicial": parm_dict.get("valor_inicial"),
                "data_inicio": parm_dict.get("data_inicio"),
                "data_fim": parm_dict.get("data_fim"),
                "id_instituicao": parm_dict.get("id_instituicao"),
            }

            id_investimento = self.execute_dml_command_parms(cmdSql, parms)
            return id_investimento

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_investment(self, parm_dict: dict):
        rotina = 'update_investment'

        try:
            cmdSql = """
                UPDATE investimento
                SET
                    id_categoria        = %(id_categoria)s,
                    ch_rede             = %(ch_rede)s,
                    nome_investimento         = %(nome_investimento)s,
                    valor_inicial               = %(valor_inicial)s,
                    data_inicio    = %(data_inicio)s,
                    data_fim  = %(data_fim)s,
                    instituicao      = %(instituicao)s
                WHERE id_investimento = %(id_investimento)s
            """

            params = {
                "id_investimento": parm_dict["id_investimento"],
                "id_categoria": parm_dict["id_categoria"],
                "ch_rede": parm_dict["ch_rede"],
                "nome_investimento": parm_dict.get("nome_investimento"),
                "valor_inicial": parm_dict["valor_inicial"],
                "data_inicio": parm_dict["data_inicio"],
                "data_fim": parm_dict.get("data_fim"),
                "instituicao": parm_dict.get("instituicao"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_investment(
            self,
            id_investimento: int,
            ch_rede: str
    ):
        rotina = 'delete_investment'

        try:
            cmdSql = """
                DELETE FROM investimento
                WHERE id_investimento = %(id_investimento)s
                and ch_rede = %(ch_rede)s
            """

            params = {
                'id_investimento': id_investimento,
                'ch_rede': ch_rede
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
