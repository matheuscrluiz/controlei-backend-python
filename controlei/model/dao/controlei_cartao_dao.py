import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiCartaoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_cartao(
            self,
            id_cartao: int = None,
            id_conta: int = None,
            id_usuario: int = None,
    ) -> dict:
        rotina = 'get_cartao'

        try:
            # Join na conta pra permitir filtrar por usuário e trazer contexto.
            query = """
                SELECT
                    ca.*,
                    c.apelido AS apelido_conta,
                    c.id_usuario
                FROM cartao ca
                JOIN conta c
                    ON c.id_conta = ca.id_conta
                where 1=1
            """

            params = {}

            if id_cartao:
                query += " and ca.id_cartao = %(id_cartao)s"
                params['id_cartao'] = id_cartao
            if id_conta:
                query += " and ca.id_conta = %(id_conta)s"
                params['id_conta'] = id_conta
            if id_usuario:
                query += " and c.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_cartao(self, parm_dict: dict):
        rotina = 'insert_cartao'

        try:
            cmdSql = """
                INSERT INTO cartao (
                    id_conta, id_cartao_pai, apelido, funcao, bandeira,
                    ultimos4, limite, dia_fechamento, dia_vencimento
                )
                VALUES (
                    %(id_conta)s, %(id_cartao_pai)s, %(apelido)s, %(funcao)s,
                    %(bandeira)s, %(ultimos4)s, %(limite)s,
                    %(dia_fechamento)s, %(dia_vencimento)s
                )
                RETURNING id_cartao
            """

            params = {
                "id_conta": parm_dict.get("id_conta"),
                "id_cartao_pai": parm_dict.get("id_cartao_pai"),
                "apelido": parm_dict.get("apelido"),
                "funcao": parm_dict.get("funcao"),
                "bandeira": parm_dict.get("bandeira"),
                "ultimos4": parm_dict.get("ultimos4"),
                "limite": parm_dict.get("limite"),
                "dia_fechamento": parm_dict.get("dia_fechamento"),
                "dia_vencimento": parm_dict.get("dia_vencimento"),
            }

            id_cartao = self.execute_dml_command_parms(cmdSql, params)
            return id_cartao

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_cartao(self, parm_dict: dict):
        rotina = 'update_cartao'

        try:
            # id_conta não muda numa edição de cartão.
            cmdSql = """
                UPDATE cartao
                SET
                    id_cartao_pai  = %(id_cartao_pai)s,
                    apelido        = %(apelido)s,
                    funcao         = %(funcao)s,
                    bandeira       = %(bandeira)s,
                    ultimos4       = %(ultimos4)s,
                    limite         = %(limite)s,
                    dia_fechamento = %(dia_fechamento)s,
                    dia_vencimento = %(dia_vencimento)s
                WHERE id_cartao = %(id_cartao)s
            """

            params = {
                "id_cartao": parm_dict["id_cartao"],
                "id_cartao_pai": parm_dict.get("id_cartao_pai"),
                "apelido": parm_dict.get("apelido"),
                "funcao": parm_dict.get("funcao"),
                "bandeira": parm_dict.get("bandeira"),
                "ultimos4": parm_dict.get("ultimos4"),
                "limite": parm_dict.get("limite"),
                "dia_fechamento": parm_dict.get("dia_fechamento"),
                "dia_vencimento": parm_dict.get("dia_vencimento"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_cartao(
            self,
            id_cartao: int,
    ):
        rotina = 'delete_cartao'

        try:
            cmdSql = """
                DELETE FROM cartao
                WHERE id_cartao = %(id_cartao)s
            """

            params = {
                'id_cartao': id_cartao,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
