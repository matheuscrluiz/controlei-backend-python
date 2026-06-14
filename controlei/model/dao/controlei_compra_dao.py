import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiCompraDAO(base.DAOBase):
    """
    DAO da compra (pai) e das parcelas (filhas). A parcela não é manipulada
    isoladamente — vive sempre via a compra, por isso fica aqui junto.
    """

    def __init__(self):
        super().__init__()

    # ---------------------- COMPRA ----------------------
    def get_compra(
            self,
            id_compra: int = None,
            id_cartao: int = None,
            id_usuario: int = None,
    ) -> dict:
        rotina = 'get_compra'

        try:
            query = """
                SELECT
                    cp.*,
                    ca.apelido AS apelido_cartao,
                    co.id_usuario,
                    cat.dsc_categoria
                FROM compra cp
                JOIN cartao ca  ON ca.id_cartao = cp.id_cartao
                JOIN conta  co  ON co.id_conta  = ca.id_conta
                LEFT JOIN categoria cat ON cat.id_categoria = cp.id_categoria
                where 1=1
            """

            params = {}

            if id_compra:
                query += " and cp.id_compra = %(id_compra)s"
                params['id_compra'] = id_compra
            if id_cartao:
                query += " and cp.id_cartao = %(id_cartao)s"
                params['id_cartao'] = id_cartao
            if id_usuario:
                query += " and co.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_compra(self, parm_dict: dict):
        rotina = 'insert_compra'

        try:
            cmdSql = """
                INSERT INTO compra (
                    id_cartao, id_categoria, dsc_compra, valor_total,
                    data_compra, num_parcelas, pre_existente
                )
                VALUES (
                    %(id_cartao)s, %(id_categoria)s, %(dsc_compra)s,
                    %(valor_total)s, %(data_compra)s, %(num_parcelas)s,
                    %(pre_existente)s
                )
                RETURNING id_compra
            """

            params = {
                "id_cartao": parm_dict.get("id_cartao"),
                "id_categoria": parm_dict.get("id_categoria"),
                "dsc_compra": parm_dict.get("dsc_compra"),
                "valor_total": parm_dict.get("valor_total"),
                "data_compra": parm_dict.get("data_compra"),
                "num_parcelas": parm_dict.get("num_parcelas"),
                "pre_existente": parm_dict.get("pre_existente") or False,
            }

            id_compra = self.execute_dml_command_parms(cmdSql, params)
            return id_compra

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_compra(self, parm_dict: dict):
        rotina = 'update_compra'

        try:
            # Edição:descrição e categoria. Valor/nº de parcelas não mudam
            # aqui — alterar isso exigiria regerar as parcelas.
            cmdSql = """
                UPDATE compra
                SET
                    dsc_compra   = %(dsc_compra)s,
                    id_categoria = %(id_categoria)s
                WHERE id_compra = %(id_compra)s
            """

            params = {
                "id_compra": parm_dict["id_compra"],
                "dsc_compra": parm_dict.get("dsc_compra"),
                "id_categoria": parm_dict.get("id_categoria"),
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def marcar_cancelada(self, id_compra: int):
        rotina = 'marcar_cancelada'

        try:
            cmdSql = """
                UPDATE compra
                SET cancelada = true
                WHERE id_compra = %(id_compra)s
            """

            params = {'id_compra': id_compra}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_compra(self, id_compra: int):
        rotina = 'delete_compra'

        try:
            # ON DELETE CASCADE remove as parcelas junto.
            cmdSql = """
                DELETE FROM compra
                WHERE id_compra = %(id_compra)s
            """

            params = {'id_compra': id_compra}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # ---------------------- PARCELA ----------------------
    def get_parcelas(
            self,
            id_compra: int = None,
            id_fatura: int = None,
    ) -> dict:
        rotina = 'get_parcelas'

        try:
            query = """
                SELECT
                    p.*,
                    c.dsc_compra,
                    c.data_compra,
                    c.num_parcelas
                FROM parcela p
                JOIN compra c ON c.id_compra = p.id_compra
                where 1=1
            """

            params = {}

            if id_compra:
                query += " and p.id_compra = %(id_compra)s"
                params['id_compra'] = id_compra
            if id_fatura:
                query += " and p.id_fatura = %(id_fatura)s"
                params['id_fatura'] = id_fatura

            query += " order by p.id_compra, p.numero"

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_parcela(self, parm_dict: dict):
        rotina = 'insert_parcela'

        try:
            cmdSql = """
                INSERT INTO parcela (
                    id_compra, id_fatura, numero, valor_parcela
                )
                VALUES (
                    %(id_compra)s, %(id_fatura)s, %(numero)s, %(valor_parcela)s
                )
                RETURNING id_parcela
            """

            params = {
                "id_compra": parm_dict.get("id_compra"),
                "id_fatura": parm_dict.get("id_fatura"),
                "numero": parm_dict.get("numero"),
                "valor_parcela": parm_dict.get("valor_parcela"),
            }

            id_parcela = self.execute_dml_command_parms(cmdSql, params)
            return id_parcela

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
