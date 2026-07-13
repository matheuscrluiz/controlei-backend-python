"""
Resolve o DONO (id_usuario) de um recurso a partir do seu id — usado pelo
guarda de autorização (anti-IDOR por recurso).

Cada entrada de RESOLVEDORES mapeia o nome do parâmetro (como viaja nas
rotas) para a query que devolve o id_usuario dono. Dono NULL significa
recurso GLOBAL (ex.: categoria/instituição do sistema) e é permitido.
"""
import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base

_VIA_CONTA = """
    SELECT id_usuario AS dono FROM conta WHERE id_conta = %(id)s
"""

_VIA_CARTAO = """
    SELECT co.id_usuario AS dono
    FROM cartao ca JOIN conta co ON co.id_conta = ca.id_conta
    WHERE ca.id_cartao = %(id)s
"""

RESOLVEDORES = {
    'id_conta': _VIA_CONTA,
    'id_conta_origem': _VIA_CONTA,
    'id_conta_destino': _VIA_CONTA,
    'id_cartao': _VIA_CARTAO,
    'id_fatura': """
        SELECT co.id_usuario AS dono
        FROM fatura f
        JOIN cartao ca ON ca.id_cartao = f.id_cartao
        JOIN conta  co ON co.id_conta  = ca.id_conta
        WHERE f.id_fatura = %(id)s
    """,
    'id_compra': """
        SELECT co.id_usuario AS dono
        FROM compra cp
        JOIN cartao ca ON ca.id_cartao = cp.id_cartao
        JOIN conta  co ON co.id_conta  = ca.id_conta
        WHERE cp.id_compra = %(id)s
    """,
    'id_lancamento': """
        SELECT co.id_usuario AS dono
        FROM lancamento l JOIN conta co ON co.id_conta = l.id_conta
        WHERE l.id_lancamento = %(id)s
    """,
    'id_cofre': """
        SELECT co.id_usuario AS dono
        FROM cofre cf JOIN conta co ON co.id_conta = cf.id_conta
        WHERE cf.id_cofre = %(id)s
    """,
    'id_recorrencia': """
        SELECT COALESCE(co.id_usuario, co2.id_usuario) AS dono
        FROM recorrencia r
        LEFT JOIN conta co ON co.id_conta = r.id_conta
        LEFT JOIN cartao ca ON ca.id_cartao = r.id_cartao
        LEFT JOIN conta co2 ON co2.id_conta = ca.id_conta
        WHERE r.id_recorrencia = %(id)s
    """,
    'id_transferencia': """
        SELECT co.id_usuario AS dono
        FROM transferencia t
        JOIN conta co ON co.id_conta = t.id_conta_origem
        WHERE t.id_transferencia = %(id)s
    """,
    'id_orcamento': """
        SELECT id_usuario AS dono FROM orcamento
        WHERE id_orcamento = %(id)s
    """,
    'id_categoria': """
        SELECT id_usuario AS dono FROM categoria
        WHERE id_categoria = %(id)s
    """,
    'id_instituicao': """
        SELECT id_usuario AS dono FROM instituicao
        WHERE id_instituicao = %(id)s
    """,
    'id_fatura_item': """
        SELECT co.id_usuario AS dono
        FROM fatura_item i
        JOIN fatura f  ON f.id_fatura  = i.id_fatura
        JOIN cartao ca ON ca.id_cartao = f.id_cartao
        JOIN conta  co ON co.id_conta  = ca.id_conta
        WHERE i.id_fatura_item = %(id)s
    """,
    'id_parcela': """
        SELECT co.id_usuario AS dono
        FROM parcela p
        JOIN fatura f  ON f.id_fatura  = p.id_fatura
        JOIN cartao ca ON ca.id_cartao = f.id_cartao
        JOIN conta  co ON co.id_conta  = ca.id_conta
        WHERE p.id_parcela = %(id)s
    """,
}

# Sentinela: distingue "recurso não existe" de "dono é NULL (global)".
NAO_ENCONTRADO = object()


class ControleiPosseDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def obter_dono(self, nome_param: str, valor_id):
        """Retorna o id_usuario dono do recurso, None se o recurso é
        global (dono NULL), ou NAO_ENCONTRADO se o registro não existe
        (a rota dá o erro natural de 'não encontrado')."""
        rotina = 'obter_dono'

        query = RESOLVEDORES.get(nome_param)
        if not query:
            return NAO_ENCONTRADO

        try:
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id': valor_id})
            linhas = self.convert_dataframe_to_dict(dataframe)
            if not linhas:
                return NAO_ENCONTRADO
            dono = linhas[0].get('dono')
            return int(dono) if dono is not None else None

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
