import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiCofreDAO(base.DAOBase):
    """Cofre (meta + investimento unificados) e suas movimentações."""

    def __init__(self):
        super().__init__()

    # ---------------------- COFRE ----------------------
    def get_cofre(
            self,
            id_cofre: int = None,
            id_conta: int = None,
            id_usuario: int = None,
    ) -> dict:
        rotina = 'get_cofre'

        try:
            # aportado = soma dos aportes - resgates (dado do próprio cofre).
            query = """
                SELECT
                    cf.*,
                    co.id_usuario,
                    COALESCE((
                        SELECT SUM(CASE WHEN m.tipo = 'aporte'
                                        THEN m.valor ELSE -m.valor END)
                        FROM cofre_movimentacao m
                        WHERE m.id_cofre = cf.id_cofre
                    ), 0) AS aportado
                FROM cofre cf
                JOIN conta co ON co.id_conta = cf.id_conta
                where 1=1
            """

            params = {}

            if id_cofre:
                query += " and cf.id_cofre = %(id_cofre)s"
                params['id_cofre'] = id_cofre
            if id_conta:
                query += " and cf.id_conta = %(id_conta)s"
                params['id_conta'] = id_conta
            if id_usuario:
                query += " and co.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_cofre(self, parm_dict: dict):
        rotina = 'insert_cofre'

        try:
            cmdSql = """
                INSERT INTO cofre (
                    id_conta, dsc_cofre, valor_alvo, valor_atual_inform,
                    data_valor_atual, prioridade
                )
                VALUES (
                    %(id_conta)s, %(dsc_cofre)s, %(valor_alvo)s,
                    %(valor_atual_inform)s,
                    %(data_valor_atual)s, %(prioridade)s
                )
                RETURNING id_cofre
            """

            params = {
                "id_conta": parm_dict.get("id_conta"),
                "dsc_cofre": parm_dict.get("dsc_cofre"),
                "valor_alvo": parm_dict.get("valor_alvo"),
                "valor_atual_inform": parm_dict.get("valor_atual_inform"),
                "data_valor_atual": parm_dict.get("data_valor_atual"),
                "prioridade": parm_dict.get("prioridade"),
            }

            id_cofre = self.execute_dml_command_parms(cmdSql, params)
            return id_cofre

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_cofre(self, parm_dict: dict):
        rotina = 'update_cofre'

        try:
            cmdSql = """
                UPDATE cofre
                SET
                    dsc_cofre  = %(dsc_cofre)s,
                    valor_alvo = %(valor_alvo)s,
                    prioridade = %(prioridade)s
                WHERE id_cofre = %(id_cofre)s
            """

            params = {
                "id_cofre": parm_dict["id_cofre"],
                "dsc_cofre": parm_dict.get("dsc_cofre"),
                "valor_alvo": parm_dict.get("valor_alvo"),
                "prioridade": parm_dict.get("prioridade"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_valor_atual(self, parm_dict: dict):
        rotina = 'update_valor_atual'

        try:
            cmdSql = """
                UPDATE cofre
                SET
                    valor_atual_inform = %(valor_atual_inform)s,
                    data_valor_atual   = %(data_valor_atual)s
                WHERE id_cofre = %(id_cofre)s
            """

            params = {
                "id_cofre": parm_dict["id_cofre"],
                "valor_atual_inform": parm_dict.get("valor_atual_inform"),
                "data_valor_atual": parm_dict.get("data_valor_atual"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_cofre(self, id_cofre: int):
        rotina = 'delete_cofre'

        try:
            # ON DELETE CASCADE remove as movimentações junto.
            cmdSql = """
                DELETE FROM cofre
                WHERE id_cofre = %(id_cofre)s
            """

            params = {'id_cofre': id_cofre}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # ---------------------- MOVIMENTAÇÃO ----------------------
    def get_movimentacoes(self, id_cofre: int = None) -> dict:
        rotina = 'get_movimentacoes'

        try:
            query = """
                SELECT * FROM cofre_movimentacao
                where 1=1
            """

            params = {}

            if id_cofre:
                query += " and id_cofre = %(id_cofre)s"
                params['id_cofre'] = id_cofre

            query += " order by data, id_cofre_mov"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_movimentacao(self, parm_dict: dict):
        rotina = 'insert_movimentacao'

        try:
            cmdSql = """
                INSERT INTO cofre_movimentacao (
                    id_cofre, id_lancamento, tipo, valor, data
                )
                VALUES (
                    %(id_cofre)s, %(id_lancamento)s, %(tipo)s,
                    %(valor)s, %(data)s
                )
                RETURNING id_cofre_mov
            """

            params = {
                "id_cofre": parm_dict.get("id_cofre"),
                "id_lancamento": parm_dict.get("id_lancamento"),
                "tipo": parm_dict.get("tipo"),
                "valor": parm_dict.get("valor"),
                "data": parm_dict.get("data"),
            }

            id_mov = self.execute_dml_command_parms(cmdSql, params)
            return id_mov

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
