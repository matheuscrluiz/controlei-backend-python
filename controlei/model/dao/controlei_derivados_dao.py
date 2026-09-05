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

    def upsert_patrimonio_snapshot(self, id_usuario: int):
        """
        Grava (ou atualiza) a posição de HOJE do usuário
          em patrimonio_snapshot,
        usando a MESMA fórmula do get_patrimonio — o snapshot reflete
        exatamente o que o dashboard mostra. Idempotente por dia (UPSERT).
        """
        rotina = 'upsert_patrimonio_snapshot'

        try:
            cmdSql = """
                INSERT INTO patrimonio_snapshot
                    (id_usuario, data, saldos,
                      cofres, divida_cartao, patrimonio)
                SELECT
                    %(id_usuario)s, CURRENT_DATE,
                    s.saldos, s.cofres, s.divida,
                    (s.saldos + s.cofres - s.divida)
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
                                                 THEN m.valor
                                                   ELSE -m.valor END)
                                 FROM cofre_movimentacao m
                                 WHERE m.id_cofre = cf.id_cofre), 0))), 0)
                         FROM cofre cf
                         JOIN conta co ON co.id_conta = cf.id_conta
                         WHERE co.id_usuario = %(id_usuario)s) AS cofres,

                        (SELECT COALESCE(SUM(
                             COALESCE((SELECT SUM(p.valor_parcela)
                               FROM parcela p
                                       WHERE p.id_fatura = f.id_fatura), 0)
                           + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                                       WHERE i.id_fatura = f.id_fatura), 0)), 0)
                         FROM fatura f
                         JOIN cartao ca ON ca.id_cartao = f.id_cartao
                         JOIN conta  co ON co.id_conta  = ca.id_conta
                         WHERE co.id_usuario = %(id_usuario)s
                           AND f.status <> 'paga') AS divida
                ) s
                ON CONFLICT (id_usuario, data) DO UPDATE SET
                    saldos        = EXCLUDED.saldos,
                    cofres        = EXCLUDED.cofres,
                    divida_cartao = EXCLUDED.divida_cartao,
                    patrimonio    = EXCLUDED.patrimonio
            """
            self.execute_dml_command_parms(cmdSql, {'id_usuario': id_usuario})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_patrimonio_historico(
            self, id_usuario: int, dias: int = 180) -> dict:
        """Série de snapshots dos últimos N dias (mais antigo primeiro)."""
        rotina = 'get_patrimonio_historico'

        try:
            query = """
                SELECT data, saldos, cofres, divida_cartao, patrimonio
                FROM patrimonio_snapshot
                WHERE id_usuario = %(id_usuario)s
                  AND data >= CURRENT_DATE - (%(dias)s || ' days')::interval
                ORDER BY data
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_usuario': id_usuario, 'dias': dias})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_ids_usuarios(self) -> dict:
        """Todos os usuários (pro cron gravar o snapshot de cada um)."""
        rotina = 'get_ids_usuarios'
        try:
            dataframe = pd.read_sql(
                sql="SELECT id_usuario FROM usuario ORDER BY id_usuario",
                con=self.get_connection())
            return self.convert_dataframe_to_dict(dataframe)
        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_projecao(self, id_usuario: int) -> dict:
        """
        Projeção de saldo até o FIM DO MÊS CORRENTE:
          saldo_atual
          + receitas previstas  (recorrências de receita em conta, ativas,
                                 com dia_do_mes ainda por vir e ainda não
                                 geradas neste mês)
          - despesas previstas  (idem, natureza despesa, em conta)
          - faturas a vencer    (faturas não pagas com vencimento até o fim
                                 do mês)
          = saldo_projetado
        Devolve também o detalhamento de cada parcela do cálculo.
        Recorrências de CARTÃO não entram (viram compra → já estão na fatura).
        """
        rotina = 'get_projecao'

        try:
            query = """
                WITH saldo AS (
                    SELECT COALESCE(SUM(l.valor), 0) AS saldo_atual
                    FROM lancamento l
                    JOIN conta co ON co.id_conta = l.id_conta
                    WHERE co.id_usuario = %(id_usuario)s
                      AND l.status = 'efetivado'
                ),
                rec AS (
                    SELECT r.id_recorrencia, r.dsc_recorrencia, r.natureza,
                           r.valor, r.dia_do_mes
                    FROM recorrencia r
                    WHERE r.id_usuario = %(id_usuario)s
                      AND r.ativa = true
                      AND r.id_conta IS NOT NULL
                      AND r.id_cartao IS NULL
                      AND r.natureza IN ('receita', 'despesa')
                      AND r.dia_do_mes > EXTRACT(DAY FROM CURRENT_DATE)
                      AND NOT EXISTS (
                            SELECT 1 FROM lancamento l2
                            WHERE l2.id_recorrencia = r.id_recorrencia
                              AND date_trunc('month', l2.data)
                                  = date_trunc('month', CURRENT_DATE)
                      )
                ),
                fat AS (
                    SELECT f.id_fatura, ca.apelido,
                      co.apelido AS apelido_conta,
                           ca.ultimos4, f.data_vencimento,
                           COALESCE((SELECT SUM(p.valor_parcela) FROM parcela p
                                     WHERE p.id_fatura = f.id_fatura), 0)
                         + COALESCE((SELECT SUM(i.valor) FROM fatura_item i
                                     WHERE i.id_fatura = f.id_fatura), 0)
                           AS valor
                    FROM fatura f
                    JOIN cartao ca ON ca.id_cartao = f.id_cartao
                    JOIN conta co ON co.id_conta = ca.id_conta
                    WHERE co.id_usuario = %(id_usuario)s
                      AND f.status <> 'paga'
                      -- inclui VENCIDAS não pagas (dinheiro que vai sair,
                      -- só que atrasado) e as que vencem até o fim do mês
                      AND f.data_vencimento <= (date_trunc('month', CURRENT_DATE)
                                                + interval '1 month - 1 day')::date
                )
                SELECT
                    (SELECT saldo_atual FROM saldo) AS saldo_atual,
                    COALESCE((SELECT SUM(valor) FROM rec
                              WHERE natureza = 'receita'), 0) AS receitas_previstas,
                    COALESCE((SELECT SUM(valor) FROM rec
                              WHERE natureza = 'despesa'), 0) AS despesas_previstas,
                    COALESCE((SELECT SUM(valor) FROM fat), 0) AS faturas_a_vencer,
                    COALESCE((SELECT json_agg(json_build_object(
                        'descricao', dsc_recorrencia, 'natureza', natureza,
                        'valor', valor, 'dia', dia_do_mes)
                        ORDER BY dia_do_mes) FROM rec), '[]'::json) AS recorrencias,
                    COALESCE((SELECT json_agg(json_build_object(
                        'descricao', apelido, 'conta', apelido_conta,
                        'ultimos4', ultimos4,
                        'vencimento', data_vencimento, 'valor', valor,
                        'atrasada', (data_vencimento < CURRENT_DATE))
                        ORDER BY data_vencimento) FROM fat), '[]'::json) AS faturas
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_usuario': id_usuario})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_recentes(self, id_usuario: int, limite: int = 15) -> dict:
        """
        Últimas movimentações do usuário, UNIFICADAS: compras no cartão e
        lançamentos em conta (receita/despesa), ordenadas da mais recente.
        Alimenta o card "Últimos registros" do dashboard — o lugar de
        conferir/corrigir o que acabou de ser registrado.
        """
        rotina = 'get_recentes'

        try:
            query = """
                SELECT * FROM (
                    SELECT
                        'compra'            AS origem,
                        cp.id_compra        AS id_registro,
                        cp.dsc_compra       AS descricao,
                        cp.valor_total      AS valor,
                        cp.data_compra      AS data,
                        'despesa'           AS natureza,
                        cp.num_parcelas     AS num_parcelas,
                        ca.apelido          AS conta_ou_cartao,
                        cp.id_cartao        AS id_cartao,
                        NULL::integer       AS id_conta,
                        cp.id_categoria     AS id_categoria,
                        cat.dsc_categoria   AS dsc_categoria,
                        cp.cancelada        AS cancelada
                    FROM compra cp
                    JOIN cartao ca   ON ca.id_cartao = cp.id_cartao
                    JOIN conta co    ON co.id_conta = ca.id_conta
                    LEFT JOIN categoria cat
                        ON cat.id_categoria = cp.id_categoria
                    WHERE co.id_usuario = %(id_usuario)s
                      AND cp.cancelada = false

                    UNION ALL

                    SELECT
                        'lancamento'        AS origem,
                        l.id_lancamento     AS id_registro,
                        l.descricao         AS descricao,
                        ABS(l.valor)        AS valor,
                        l.data              AS data,
                        l.natureza          AS natureza,
                        NULL::integer       AS num_parcelas,
                        co.apelido          AS conta_ou_cartao,
                        NULL::integer       AS id_cartao,
                        l.id_conta          AS id_conta,
                        l.id_categoria      AS id_categoria,
                        cat.dsc_categoria   AS dsc_categoria,
                        false               AS cancelada
                    FROM lancamento l
                    JOIN conta co ON co.id_conta = l.id_conta
                    LEFT JOIN categoria cat
                      ON cat.id_categoria = l.id_categoria
                    WHERE co.id_usuario = %(id_usuario)s
                      AND l.natureza IN ('receita', 'despesa')
                      AND l.status = 'efetivado'
                ) t
                ORDER BY t.data DESC, t.id_registro DESC
                LIMIT %(limite)s
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id_usuario': id_usuario, 'limite': limite})
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
            raise DAOException(__file__, rotina, erro)

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
        """Patrimônio líquido = saldos + valor dos cofres
          - dívida de cartão."""
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
                                                 THEN m.valor
                                                   ELSE -m.valor END)
                                 FROM cofre_movimentacao m
                                 WHERE m.id_cofre = cf.id_cofre), 0))), 0)
                         FROM cofre cf
                         JOIN conta co ON co.id_conta = cf.id_conta
                         WHERE co.id_usuario = %(id_usuario)s) AS cofres,

                        (SELECT COALESCE(SUM(
                             COALESCE((SELECT SUM(p.valor_parcela)
                               FROM parcela p
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
