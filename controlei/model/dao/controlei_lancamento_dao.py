import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiLancamentoDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_lancamento(
            self,
            id_lancamento: int = None,
            id_conta: int = None,
            id_usuario: int = None,
            natureza: str = None,
            status: str = None,
            id_transferencia: int = None,
            id_recorrencia: int = None,
            data_inicio=None,
            data_fim=None,
    ) -> dict:
        rotina = 'get_lancamento'

        try:
            query = """
                SELECT
                    l.*,
                    co.id_usuario,
                    cat.dsc_categoria,
                    ca.apelido AS apelido_cartao
                FROM lancamento l
                JOIN conta co ON co.id_conta = l.id_conta
                LEFT JOIN categoria cat ON cat.id_categoria = l.id_categoria
                LEFT JOIN cartao ca ON ca.id_cartao = l.id_cartao
                where 1=1
            """

            params = {}

            if id_lancamento:
                query += " and l.id_lancamento = %(id_lancamento)s"
                params['id_lancamento'] = id_lancamento
            if id_conta:
                query += " and l.id_conta = %(id_conta)s"
                params['id_conta'] = id_conta
            if id_usuario:
                query += " and co.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario
            if natureza:
                query += " and l.natureza = %(natureza)s"
                params['natureza'] = natureza
            if status:
                query += " and l.status = %(status)s"
                params['status'] = status
            if id_transferencia:
                query += " and l.id_transferencia = %(id_transferencia)s"
                params['id_transferencia'] = id_transferencia
            if id_recorrencia:
                query += " and l.id_recorrencia = %(id_recorrencia)s"
                params['id_recorrencia'] = id_recorrencia
            if data_inicio:
                query += " and l.data >= %(data_inicio)s"
                params['data_inicio'] = data_inicio
            if data_fim:
                query += " and l.data <= %(data_fim)s"
                params['data_fim'] = data_fim

            query += " order by l.data desc, l.id_lancamento desc"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_lancamento(self, parm_dict: dict):
        rotina = 'insert_lancamento'

        try:
            cmdSql = """
                INSERT INTO lancamento (
                    id_conta, id_categoria, id_cartao, id_transferencia,
                    id_recorrencia, natureza, valor, data, descricao, status
                )
                VALUES (
                    %(id_conta)s, %(id_categoria)s, %(id_cartao)s,
                    %(id_transferencia)s, %(id_recorrencia)s, %(natureza)s,
                    %(valor)s, %(data)s, %(descricao)s, %(status)s
                )
                RETURNING id_lancamento
            """

            params = {
                "id_conta": parm_dict.get("id_conta"),
                "id_categoria": parm_dict.get("id_categoria"),
                "id_cartao": parm_dict.get("id_cartao"),
                "id_transferencia": parm_dict.get("id_transferencia"),
                "id_recorrencia": parm_dict.get("id_recorrencia"),
                "natureza": parm_dict.get("natureza"),
                "valor": parm_dict.get("valor"),
                "data": parm_dict.get("data"),
                "descricao": parm_dict.get("descricao"),
                "status": parm_dict.get("status") or 'efetivado',
            }

            id_lancamento = self.execute_dml_command_parms(cmdSql, params)
            return id_lancamento

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_lancamento(self, parm_dict: dict):
        rotina = 'update_lancamento'

        try:
            cmdSql = """
                UPDATE lancamento
                SET
                    id_categoria = %(id_categoria)s,
                    id_cartao    = %(id_cartao)s,
                    natureza     = %(natureza)s,
                    valor        = %(valor)s,
                    data         = %(data)s,
                    descricao    = %(descricao)s
                WHERE id_lancamento = %(id_lancamento)s
            """

            params = {
                "id_lancamento": parm_dict["id_lancamento"],
                "id_categoria": parm_dict.get("id_categoria"),
                "id_cartao": parm_dict.get("id_cartao"),
                "natureza": parm_dict.get("natureza"),
                "valor": parm_dict.get("valor"),
                "data": parm_dict.get("data"),
                "descricao": parm_dict.get("descricao"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_status_lancamento(self, id_lancamento: int, status: str):
        rotina = 'update_status_lancamento'

        try:
            cmdSql = """
                UPDATE lancamento
                SET status = %(status)s
                WHERE id_lancamento = %(id_lancamento)s
            """

            params = {"id_lancamento": id_lancamento, "status": status}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_lancamento(self, id_lancamento: int):
        rotina = 'delete_lancamento'

        try:
            cmdSql = """
                DELETE FROM lancamento
                WHERE id_lancamento = %(id_lancamento)s
            """

            params = {'id_lancamento': id_lancamento}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
