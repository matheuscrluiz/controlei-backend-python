import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiFaturaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_fatura(
            self,
            id_fatura: int = None,
            id_cartao: int = None,
            status: str = None,
            competencia=None,
            id_usuario: int = None,
    ) -> dict:
        rotina = 'get_fatura'

        try:
            # O VALOR da fatura é derivado (get_fatura_total) — não vem daqui.
            query = """
                SELECT
                    f.*,
                    ca.apelido AS apelido_cartao,
                    ca.id_conta,
                    co.id_usuario
                FROM fatura f
                JOIN cartao ca ON ca.id_cartao = f.id_cartao
                JOIN conta  co ON co.id_conta  = ca.id_conta
                where 1=1
            """

            params = {}

            if id_fatura:
                query += " and f.id_fatura = %(id_fatura)s"
                params['id_fatura'] = id_fatura
            if id_cartao:
                query += " and f.id_cartao = %(id_cartao)s"
                params['id_cartao'] = id_cartao
            if status:
                query += " and f.status = %(status)s"
                params['status'] = status
            if competencia:
                query += " and f.competencia = %(competencia)s"
                params['competencia'] = competencia
            if id_usuario:
                query += " and co.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_fatura(self, parm_dict: dict):
        rotina = 'insert_fatura'

        try:
            cmdSql = """
                INSERT INTO fatura (
                    id_cartao, competencia, data_fechamento,
                    data_vencimento, status
                )
                VALUES (
                    %(id_cartao)s, %(competencia)s, %(data_fechamento)s,
                    %(data_vencimento)s, %(status)s
                )
                RETURNING id_fatura
            """

            params = {
                "id_cartao": parm_dict.get("id_cartao"),
                "competencia": parm_dict.get("competencia"),
                "data_fechamento": parm_dict.get("data_fechamento"),
                "data_vencimento": parm_dict.get("data_vencimento"),
                "status": parm_dict.get("status") or 'aberta',
            }

            id_fatura = self.execute_dml_command_parms(cmdSql, params)
            return id_fatura

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_total(self, id_fatura: int):
        """Total a pagar da fatura = parcelas + itens avulsos (encargos somam,
        créditos abatem). Mesma lógica do relatório, computada no servidor."""
        rotina = 'get_total'

        try:
            query = """
                SELECT
                    COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                              WHERE p.id_fatura = %(id_fatura)s), 0)
                  + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                              WHERE i.id_fatura = %(id_fatura)s), 0) AS valor
            """

            params = {'id_fatura': id_fatura}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_faturas_a_vencer(self, id_usuario: int, dias: int = 7):
        """Faturas não pagas cujo vencimento é hoje..+dias (inclui vencidas),
        já com total derivado e dias até o vencimento."""
        rotina = 'get_faturas_a_vencer'

        try:
            query = """
                SELECT
                    f.id_fatura, f.id_cartao, f.competencia,
                    f.data_vencimento, f.data_fechamento, f.status,
                    ca.apelido AS apelido_cartao,
                    ca.ultimos4, ca.bandeira,
                    co.apelido AS apelido_conta,
                    COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                              WHERE p.id_fatura = f.id_fatura), 0)
                  + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                              WHERE i.id_fatura = f.id_fatura), 0) AS total,
                    (f.data_vencimento::date - CURRENT_DATE) AS dias_ate
                FROM fatura f
                JOIN cartao ca ON ca.id_cartao = f.id_cartao
                JOIN conta  co ON co.id_conta  = ca.id_conta
                WHERE co.id_usuario = %(id_usuario)s
                  AND f.status <> 'paga'
                  AND f.data_vencimento::date <= CURRENT_DATE + %(dias)s
                ORDER BY f.data_vencimento
            """
            params = {'id_usuario': id_usuario, 'dias': dias}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_ids_faturas_para_fechar(self):
        """IDs de faturas 'aberta' cujo fechamento já chegou (<= hoje)."""
        rotina = 'get_ids_faturas_para_fechar'

        try:
            query = """
                SELECT id_fatura
                FROM fatura
                WHERE status = 'aberta'
                  AND data_fechamento::date <= CURRENT_DATE
            """
            dataframe = pd.read_sql(sql=query, con=self.get_connection())
            linhas = self.convert_dataframe_to_dict(dataframe)
            return [linha['id_fatura'] for linha in linhas]

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_faturas_para_notificar(self):
        """Faturas não pagas com tudo que o notificador precisa: e-mail do
        dono, total, dias até vencer e os controles de notificação."""
        rotina = 'get_faturas_para_notificar'

        try:
            query = """
                SELECT
                    f.id_fatura, f.competencia, f.data_vencimento, f.status,
                    (f.data_vencimento::date - CURRENT_DATE) AS dias_ate,
                    (CURRENT_DATE - f.notif_vencida_em) AS dias_desde_vencida,
                    ca.apelido AS apelido_cartao, ca.ultimos4,
                    co.apelido AS apelido_conta,
                    u.email AS email_usuario, u.nome AS nome_usuario,
                    COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                              WHERE p.id_fatura = f.id_fatura), 0)
                  + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                              WHERE i.id_fatura = f.id_fatura), 0) AS total,
                    f.notif_fechada, f.notif_avencer_3,
                    f.notif_avencer_1, f.notif_vencida_em
                FROM fatura f
                JOIN cartao  ca ON ca.id_cartao  = f.id_cartao
                JOIN conta   co ON co.id_conta   = ca.id_conta
                JOIN usuario u  ON u.id_usuario  = co.id_usuario
                WHERE f.status <> 'paga'
                  AND (
                        (f.status = 'fechada' AND f.notif_fechada = FALSE)
                        OR f.data_vencimento::date <= CURRENT_DATE + 3
                      )
                ORDER BY f.data_vencimento
            """
            dataframe = pd.read_sql(sql=query, con=self.get_connection())
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def marcar_notif(self, id_fatura: int, campo: str, valor):
        """Marca um controle de notificação. `campo` é validado por lista."""
        rotina = 'marcar_notif'

        permitidos = {
            'notif_fechada', 'notif_avencer_3',
            'notif_avencer_1', 'notif_vencida_em',
        }
        if campo not in permitidos:
            raise DAOException(__file__, rotina, f'Campo inválido: {campo}')

        try:
            cmdSql = f"""
                UPDATE fatura
                SET {campo} = %(valor)s
                WHERE id_fatura = %(id_fatura)s
            """
            params = {'id_fatura': id_fatura, 'valor': valor}
            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_status_fatura(self, id_fatura: int, status: str):
        rotina = 'update_status_fatura'

        try:
            cmdSql = """
                UPDATE fatura
                SET status = %(status)s
                WHERE id_fatura = %(id_fatura)s
            """

            params = {
                "id_fatura": id_fatura,
                "status": status,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_fatura(self, id_fatura: int):
        rotina = 'delete_fatura'

        try:
            # Obs.: o banco barra apagar fatura que ainda tem parcelas (FK).
            cmdSql = """
                DELETE FROM fatura
                WHERE id_fatura = %(id_fatura)s
            """

            params = {'id_fatura': id_fatura}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
