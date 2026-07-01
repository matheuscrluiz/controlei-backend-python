import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiDerivadosDAO(base.DAOBase):
    """
    Leituras derivadas (o que antes eram views). Cada regra de ouro vive aqui,
    em um único lugar:
      - SALDO soma TODOS os lançamentos efetivados (qualquer natureza).
      - FLUXO mensal soma só receita/despesa (exclui transferência/ajuste).
      - PATRIMÔNIO = saldos + valor dos cofres - dívida de cartão.
    """

    def __init__(self):
        super().__init__()

    def get_saldo_conta(self, id_conta: int) -> dict:
        """Saldo de uma conta = soma dos lançamentos efetivados."""
        rotina = 'get_saldo_conta'

        try:
            query = """
                SELECT COALESCE(SUM(valor), 0) AS saldo
                FROM lancamento
                WHERE id_conta = %(id_conta)s
                  AND status = 'efetivado'
            """

            params = {'id_conta': id_conta}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_saldos_por_conta(self, id_usuario: int) -> dict:
        """Saldo de cada conta do usuário (pra home)."""
        rotina = 'get_saldos_por_conta'

        try:
            query = """
                SELECT
                    co.id_conta,
                    co.apelido,
                    COALESCE(SUM(l.valor) FILTER (
                        WHERE l.status = 'efetivado'), 0) AS saldo
                FROM conta co
                LEFT JOIN lancamento l ON l.id_conta = co.id_conta
                WHERE co.id_usuario = %(id_usuario)s
                GROUP BY co.id_conta, co.apelido
                ORDER BY co.apelido
            """

            params = {'id_usuario': id_usuario}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_fatura_total(self, id_fatura: int) -> dict:
        """Total da fatura = parcelas + itens avulsos."""
        rotina = 'get_fatura_total'

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

    def get_divida_cartao(
            self, id_cartao: int = None, id_usuario: int = None) -> dict:
        """Dívida = soma das faturas NÃO pagas (por cartão ou por usuário)."""
        rotina = 'get_divida_cartao'

        try:
            query = """
                SELECT COALESCE(SUM(t.total), 0) AS divida
                FROM (
                    SELECT
                        COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                                  WHERE p.id_fatura = f.id_fatura), 0)
                      + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                                  WHERE i.id_fatura = f.id_fatura), 0) AS total
                    FROM fatura f
                    JOIN cartao ca ON ca.id_cartao = f.id_cartao
                    JOIN conta  co ON co.id_conta  = ca.id_conta
                    WHERE f.status <> 'paga'
            """

            params = {}

            if id_cartao:
                query += " and f.id_cartao = %(id_cartao)s"
                params['id_cartao'] = id_cartao
            if id_usuario:
                query += " and co.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            query += " ) t"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_fluxo_mensal(
            self, id_usuario: int, competencia: str = None) -> dict:
        """
        Receitas, despesas e resultado por mês. REGRA DE OURO: só receita e
        despesa entram; transferência e ajuste ficam de fora.
        """
        rotina = 'get_fluxo_mensal'

        try:
            query = """
                SELECT
                    to_char(l.data, 'YYYY-MM') AS competencia,
                    COALESCE(SUM(l.valor) FILTER (
                        WHERE l.natureza = 'receita'), 0)  AS receitas,
                    COALESCE(SUM(-l.valor) FILTER (
                        WHERE l.natureza = 'despesa'), 0)  AS despesas,
                    COALESCE(SUM(l.valor), 0)              AS resultado
                FROM lancamento l
                JOIN conta co ON co.id_conta = l.id_conta
                WHERE co.id_usuario = %(id_usuario)s
                  AND l.status = 'efetivado'
                  AND l.natureza IN ('receita', 'despesa')
            """

            params = {'id_usuario': id_usuario}

            if competencia:
                query += " and to_char(l.data, 'YYYY-MM') = %(competencia)s"
                params['competencia'] = competencia

            query += " GROUP BY 1 ORDER BY 1"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, 'get_fluxo_mensal', erro)

    def get_despesas_por_categoria(
            self, id_usuario: int, data_inicio: str, data_fim: str) -> dict:
        """Gastos por categoria no período: despesas efetivadas em conta
        (lançamentos) + compras no cartão (não canceladas)."""
        rotina = 'get_despesas_por_categoria'

        try:
            query = """
                WITH gastos AS (
                    SELECT l.id_categoria AS id_categoria,
                           ABS(l.valor)  AS valor
                    FROM lancamento l
                    JOIN conta co ON co.id_conta = l.id_conta
                    WHERE co.id_usuario = %(id_usuario)s
                      AND l.status = 'efetivado'
                      AND l.natureza = 'despesa'
                      AND l.data BETWEEN %(ini)s AND %(fim)s

                    UNION ALL

                    SELECT cp.id_categoria  AS id_categoria,
                           cp.valor_total   AS valor
                    FROM compra cp
                    JOIN cartao ca ON ca.id_cartao = cp.id_cartao
                    JOIN conta co2 ON co2.id_conta = ca.id_conta
                    WHERE co2.id_usuario = %(id_usuario)s
                      AND cp.cancelada = false
                      AND cp.data_compra BETWEEN %(ini)s AND %(fim)s
                )
                SELECT
                    g.id_categoria AS id_categoria,
                    COALESCE(cat.dsc_categoria, 'Sem categoria')
                        AS dsc_categoria,
                    SUM(g.valor) AS total
                FROM gastos g
                LEFT JOIN categoria cat
                    ON cat.id_categoria = g.id_categoria
                GROUP BY g.id_categoria, cat.dsc_categoria
                ORDER BY total DESC
            """

            params = {
                'id_usuario': id_usuario,
                'ini': data_inicio,
                'fim': data_fim,
            }

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_cofre_valor(self, id_cofre: int) -> dict:
        """Valor do cofre = mercado informado; na falta, aportado líquido."""
        rotina = 'get_cofre_valor'

        try:
            query = """
                SELECT COALESCE(
                    cf.valor_atual_inform,
                    COALESCE((
                        SELECT SUM(CASE WHEN m.tipo = 'aporte'
                                        THEN m.valor ELSE -m.valor END)
                        FROM cofre_movimentacao m
                        WHERE m.id_cofre = cf.id_cofre
                    ), 0)
                ) AS valor
                FROM cofre cf
                WHERE cf.id_cofre = %(id_cofre)s
            """

            params = {'id_cofre': id_cofre}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_patrimonio_usuario(self, id_usuario: int) -> dict:
        """Patrimônio líquido = saldos + valor dos cofres - dívida de cartão."""
        rotina = 'get_patrimonio_usuario'

        try:
            query = """
                SELECT
                    s.saldos,
                    s.cofres,
                    s.divida,
                    (s.saldos + s.cofres - s.divida) AS patrimonio
                FROM (
                    SELECT
                        (SELECT COALESCE(SUM(l.valor), 0)
                         FROM lancamento l
                         JOIN conta co ON co.id_conta = l.id_conta
                         WHERE co.id_usuario = %(id_usuario)s
                           AND l.status = 'efetivado') AS saldos,

                        (SELECT COALESCE(SUM(COALESCE(
                             cf.valor_atual_inform,
                             COALESCE((
                                 SELECT SUM(CASE WHEN m.tipo = 'aporte'
                                                 THEN m.valor ELSE -m.valor END)
                                 FROM cofre_movimentacao m
                                 WHERE m.id_cofre = cf.id_cofre), 0))), 0)
                         FROM cofre cf
                         JOIN conta co ON co.id_conta = cf.id_conta
                         WHERE co.id_usuario = %(id_usuario)s) AS cofres,

                        (SELECT COALESCE(SUM(
                             COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                                       WHERE p.id_fatura = f.id_fatura), 0)
                           + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                                       WHERE i.id_fatura = f.id_fatura), 0)), 0)
                         FROM fatura f
                         JOIN cartao ca ON ca.id_cartao = f.id_cartao
                         JOIN conta  co ON co.id_conta  = ca.id_conta
                         WHERE co.id_usuario = %(id_usuario)s
                           AND f.status <> 'paga') AS divida
                ) s
            """

            params = {'id_usuario': id_usuario}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
