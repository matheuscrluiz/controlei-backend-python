import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiBeneficioDAO(base.DAOBase):
    """
    Benefícios (VA, VR, VT, cartão-presente...) e seus movimentos.

    Módulo APARTADO do núcleo financeiro: nada aqui referencia conta,
    cartão ou categoria, e nada daqui deve ser somado a patrimônio, saldos,
    fluxo ou projeção. Saldo = SUM(recargas) − SUM(gastos), calculado na
    leitura (mesmo princípio do resto do schema).
    """

    def __init__(self):
        super().__init__()

    # ---------------------- BENEFÍCIO ----------------------
    def get_beneficios(self, id_usuario: int) -> dict:
        """Benefícios do usuário com saldo atual e gasto do mês corrente."""
        rotina = 'get_beneficios'

        try:
            query = """
                SELECT b.id_beneficio, b.id_usuario, b.dsc_beneficio, b.tipo,
                       b.cor, b.dia_recarga, b.ativo, b.criado_em,
                       COALESCE(SUM(CASE WHEN m.tipo = 'recarga' THEN m.valor
                                         WHEN m.tipo = 'gasto'   THEN -m.valor
                                    END), 0)                          AS saldo,
                       COALESCE(SUM(CASE WHEN m.tipo = 'gasto'
                                          AND date_trunc('month', m.data)
                                              = date_trunc('month', CURRENT_DATE)
                                         THEN m.valor END), 0)        AS gasto_mes
                FROM beneficio b
                LEFT JOIN beneficio_movimento m
                  ON m.id_beneficio = b.id_beneficio
                WHERE b.id_usuario = %(id_usuario)s
                  AND b.ativo = true
                GROUP BY b.id_beneficio
                ORDER BY b.criado_em
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_usuario': id_usuario})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_beneficio(self, parm_dict: dict) -> int:
        rotina = 'insert_beneficio'

        try:
            cmdSql = """
                INSERT INTO beneficio
                    (id_usuario, dsc_beneficio, tipo, cor, dia_recarga)
                VALUES
                    (%(id_usuario)s, %(dsc_beneficio)s, %(tipo)s, %(cor)s,
                     %(dia_recarga)s)
                RETURNING id_beneficio
            """
            return self.execute_dml_command_parms(cmdSql, {
                'id_usuario': parm_dict.get('id_usuario'),
                'dsc_beneficio': parm_dict.get('dsc_beneficio'),
                'tipo': parm_dict.get('tipo') or 'outro',
                'cor': parm_dict.get('cor'),
                'dia_recarga': parm_dict.get('dia_recarga'),
            })

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_beneficio(self, parm_dict: dict):
        rotina = 'update_beneficio'

        try:
            cmdSql = """
                UPDATE beneficio SET
                    dsc_beneficio = COALESCE(%(dsc_beneficio)s, dsc_beneficio),
                    tipo          = COALESCE(%(tipo)s, tipo),
                    cor           = %(cor)s,
                    dia_recarga   = %(dia_recarga)s
                WHERE id_beneficio = %(id_beneficio)s
            """
            self.execute_dml_command_parms(cmdSql, {
                'id_beneficio': parm_dict.get('id_beneficio'),
                'dsc_beneficio': parm_dict.get('dsc_beneficio'),
                'tipo': parm_dict.get('tipo'),
                'cor': parm_dict.get('cor'),
                'dia_recarga': parm_dict.get('dia_recarga'),
            })

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_beneficio(self, id_beneficio: int):
        """Exclusão dura: movimentos vão junto (ON DELETE CASCADE)."""
        rotina = 'delete_beneficio'

        try:
            self.execute_dml_command_parms(
                "DELETE FROM beneficio WHERE id_beneficio = %(id)s",
                {'id': id_beneficio})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # ---------------------- MOVIMENTOS ----------------------
    def get_movimentos(self, id_beneficio: int, competencia=None) -> dict:
        """Extrato do benefício; se competencia (YYYY-MM-01), só aquele mês."""
        rotina = 'get_movimentos'

        try:
            query = """
                SELECT id_beneficio_mov, id_beneficio, tipo, valor, data,
                       descricao, criado_em
                FROM beneficio_movimento
                WHERE id_beneficio = %(id_beneficio)s
            """
            params = {'id_beneficio': id_beneficio}
            if competencia:
                query += """
                  AND date_trunc('month', data)
                      = date_trunc('month', %(competencia)s::date)
                """
                params['competencia'] = competencia
            query += " ORDER BY data DESC, id_beneficio_mov DESC"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_resumo_mes(self, id_beneficio: int, competencia) -> dict:
        """Gastei / recebi no mês + saldo atual (posição, não período)."""
        rotina = 'get_resumo_mes'

        try:
            query = """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'gasto'
                                       AND date_trunc('month', data)
                                           = date_trunc('month', %(competencia)s::date)
                                      THEN valor END), 0) AS gasto_mes,
                    COALESCE(SUM(CASE WHEN tipo = 'recarga'
                                       AND date_trunc('month', data)
                                           = date_trunc('month', %(competencia)s::date)
                                      THEN valor END), 0) AS recarga_mes,
                    COALESCE(SUM(CASE WHEN tipo = 'recarga' THEN valor
                                      WHEN tipo = 'gasto'   THEN -valor END), 0)
                                                         AS saldo
                FROM beneficio_movimento
                WHERE id_beneficio = %(id_beneficio)s
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_beneficio': id_beneficio,
                        'competencia': competencia})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_historico_mensal(self, id_beneficio: int, meses: int = 6) -> dict:
        """Gasto por mês nos últimos N meses (inclui meses sem gasto = 0)."""
        rotina = 'get_historico_mensal'

        try:
            query = """
                WITH meses AS (
                    SELECT date_trunc('month', CURRENT_DATE)
                           - (n || ' months')::interval AS competencia
                    FROM generate_series(0, %(meses)s - 1) AS n
                )
                SELECT ms.competencia::date AS competencia,
                       COALESCE(SUM(CASE WHEN m.tipo = 'gasto' THEN m.valor END), 0)
                           AS gasto,
                       COALESCE(SUM(CASE WHEN m.tipo = 'recarga' THEN m.valor END), 0)
                           AS recarga
                FROM meses ms
                LEFT JOIN beneficio_movimento m
                       ON m.id_beneficio = %(id_beneficio)s
                      AND date_trunc('month', m.data) = ms.competencia
                GROUP BY ms.competencia
                ORDER BY ms.competencia
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_beneficio': id_beneficio, 'meses': meses})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_movimento(self, parm_dict: dict):
        rotina = 'insert_movimento'

        try:
            cmdSql = """
                INSERT INTO beneficio_movimento
                    (id_beneficio, tipo, valor, data, descricao)
                VALUES
                    (%(id_beneficio)s, %(tipo)s, %(valor)s, %(data)s,
                     %(descricao)s)
            """
            self.execute_dml_command_parms(cmdSql, {
                'id_beneficio': parm_dict.get('id_beneficio'),
                'tipo': parm_dict.get('tipo'),
                'valor': parm_dict.get('valor'),
                'data': parm_dict.get('data'),
                'descricao': parm_dict.get('descricao'),
            })

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_movimento(self, parm_dict: dict):
        rotina = 'update_movimento'

        try:
            cmdSql = """
                UPDATE beneficio_movimento SET
                    valor     = COALESCE(%(valor)s, valor),
                    data      = COALESCE(%(data)s, data),
                    descricao = %(descricao)s
                WHERE id_beneficio_mov = %(id_beneficio_mov)s
            """
            self.execute_dml_command_parms(cmdSql, {
                'id_beneficio_mov': parm_dict.get('id_beneficio_mov'),
                'valor': parm_dict.get('valor'),
                'data': parm_dict.get('data'),
                'descricao': parm_dict.get('descricao'),
            })

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_movimento(self, id_beneficio_mov: int):
        rotina = 'delete_movimento'

        try:
            self.execute_dml_command_parms(
                "DELETE FROM beneficio_movimento WHERE id_beneficio_mov = %(id)s",
                {'id': id_beneficio_mov})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
