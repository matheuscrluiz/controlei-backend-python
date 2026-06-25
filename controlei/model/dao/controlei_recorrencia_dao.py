import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiRecorrenciaDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def get_recorrencia(
            self,
            id_recorrencia: int = None,
            id_usuario: int = None,
            ativa: bool = None,
            dia_do_mes: int = None,
            id_conta: int = None,
            id_cartao: int = None,
    ) -> dict:
        rotina = 'get_recorrencia'

        try:
            query = """
                SELECT r.*, cat.dsc_categoria
                FROM recorrencia r
                LEFT JOIN categoria cat ON cat.id_categoria = r.id_categoria
                where 1=1
            """

            params = {}

            if id_recorrencia:
                query += " and r.id_recorrencia = %(id_recorrencia)s"
                params['id_recorrencia'] = id_recorrencia
            if id_usuario:
                query += " and r.id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario
            if ativa is not None:
                query += " and r.ativa = %(ativa)s"
                params['ativa'] = ativa
            if dia_do_mes:
                query += " and r.dia_do_mes = %(dia_do_mes)s"
                params['dia_do_mes'] = dia_do_mes
            if id_conta:
                query += " and r.id_conta = %(id_conta)s"
                params['id_conta'] = id_conta
            if id_cartao:
                query += " and r.id_cartao = %(id_cartao)s"
                params['id_cartao'] = id_cartao

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_recorrencia(self, parm_dict: dict):
        rotina = 'insert_recorrencia'

        try:
            cmdSql = """
                INSERT INTO recorrencia (
                    id_usuario, id_conta, id_cartao, id_categoria, natureza,
                    dsc_recorrencia, valor, variavel, dia_do_mes,
                    confirmar_automatico, ativa
                )
                VALUES (
                    %(id_usuario)s, %(id_conta)s, %(id_cartao)s,
                    %(id_categoria)s, %(natureza)s, %(dsc_recorrencia)s,
                    %(valor)s, %(variavel)s, %(dia_do_mes)s,
                    %(confirmar_automatico)s, %(ativa)s
                )
                RETURNING id_recorrencia
            """

            params = {
                "id_usuario": parm_dict.get("id_usuario"),
                "id_conta": parm_dict.get("id_conta"),
                "id_cartao": parm_dict.get("id_cartao"),
                "id_categoria": parm_dict.get("id_categoria"),
                "natureza": parm_dict.get("natureza"),
                "dsc_recorrencia": parm_dict.get("dsc_recorrencia"),
                "valor": parm_dict.get("valor"),
                "variavel": parm_dict.get("variavel") or False,
                "dia_do_mes": parm_dict.get("dia_do_mes"),
                "confirmar_automatico": parm_dict.get(
                    "confirmar_automatico") or False,
                "ativa": parm_dict.get("ativa") if parm_dict.get("ativa")
                is not None else True,
            }

            id_recorrencia = self.execute_dml_command_parms(cmdSql, params)
            return id_recorrencia

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_recorrencia(self, parm_dict: dict):
        rotina = 'update_recorrencia'

        try:
            # O MEIO (id_conta/id_cartao) não muda —
            # recrie a recorrência se for
            # trocar de meio. Aqui muda o resto.
            cmdSql = """
                UPDATE recorrencia
                SET
                    id_categoria         = %(id_categoria)s,
                    natureza             = %(natureza)s,
                    dsc_recorrencia      = %(dsc_recorrencia)s,
                    valor                = %(valor)s,
                    variavel             = %(variavel)s,
                    dia_do_mes           = %(dia_do_mes)s,
                    confirmar_automatico = %(confirmar_automatico)s,
                    ativa                = %(ativa)s
                WHERE id_recorrencia = %(id_recorrencia)s
            """

            params = {
                "id_recorrencia": parm_dict["id_recorrencia"],
                "id_categoria": parm_dict.get("id_categoria"),
                "natureza": parm_dict.get("natureza"),
                "dsc_recorrencia": parm_dict.get("dsc_recorrencia"),
                "valor": parm_dict.get("valor"),
                "variavel": parm_dict.get("variavel") or False,
                "dia_do_mes": parm_dict.get("dia_do_mes"),
                "confirmar_automatico": parm_dict.get(
                    "confirmar_automatico") or False,
                "ativa": parm_dict.get("ativa") if parm_dict.get("ativa")
                is not None else True,
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_recorrencia(self, id_recorrencia: int):
        rotina = 'delete_recorrencia'

        try:
            cmdSql = """
                DELETE FROM recorrencia
                WHERE id_recorrencia = %(id_recorrencia)s
            """

            params = {'id_recorrencia': id_recorrencia}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
