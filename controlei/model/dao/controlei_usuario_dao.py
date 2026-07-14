import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class ControleiUserDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    # ------------------------------------------------------------------
    # Leitura "segura": NUNCA devolve senha_hash. Filtros opcionais.
    # ------------------------------------------------------------------
    def get_user(self, id_usuario: int = None, email: str = None) -> dict:
        rotina = 'get_user'

        try:
            query = """
                select id_usuario, nome, email, criado_em
                from usuario
                where 1=1
            """

            params = {}

            if id_usuario:
                query += " and id_usuario = %(id_usuario)s"
                params['id_usuario'] = id_usuario
            if email:
                query += " and email = %(email)s"
                params['email'] = email

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # ------------------------------------------------------------------
    # Para autenticação: inclui senha_hash. Usado pelo fluxo de login.
    # ------------------------------------------------------------------
    def get_credenciais_by_email(self, email: str) -> dict:
        rotina = 'get_credenciais_by_email'

        try:
            query = """
                select id_usuario, nome, email, senha_hash
                from usuario
                where email = %(email)s
            """

            params = {'email': email}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)

            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_usuario(self, parm_dict: dict):
        rotina = 'insert_usuario'

        try:
            cmdSql = """
                INSERT INTO usuario (nome, email, senha_hash)
                VALUES (%(nome)s, %(email)s, %(senha_hash)s)
                returning id_usuario
            """

            params = {
                "nome": parm_dict.get("nome"),
                "email": parm_dict.get("email"),
                "senha_hash": parm_dict.get("senha_hash")
            }

            id_usuario = self.execute_dml_command_parms(cmdSql, params)
            return id_usuario

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_usuario(self, parm_dict: dict):
        rotina = 'update_usuario'

        try:
            cmdSql = """
                UPDATE usuario
                SET
                    nome  = %(nome)s,
                    email = %(email)s
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": parm_dict['id_usuario'],
                "nome": parm_dict['nome'],
                "email": parm_dict['email']
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    # Troca de senha isolada: só mexe no hash.
    def update_senha(self, id_usuario: int, senha_hash: str):
        rotina = 'update_senha'

        try:
            cmdSql = """
                UPDATE usuario
                SET senha_hash = %(senha_hash)s
                WHERE id_usuario = %(id_usuario)s
            """

            params = {
                "id_usuario": id_usuario,
                "senha_hash": senha_hash
            }

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_preferencias(self, id_usuario: int) -> dict:
        rotina = 'get_preferencias'

        try:
            query = """
                select id_usuario, nome, email,
                       notif_email_ativo, notif_fechada_ativa,
                       notif_avencer_ativa, notif_vencida_ativa,
                       notif_email_destino,
                       notif_telegram_ativo,
                       (telegram_chat_id IS NOT NULL) AS telegram_vinculado,
                       walkthrough_visto, checklist_oculto
                from usuario
                where id_usuario = %(id_usuario)s
            """
            params = {'id_usuario': id_usuario}
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params)
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def update_preferencias(self, parm_dict: dict):
        rotina = 'update_preferencias'

        try:
            cmdSql = """
                UPDATE usuario SET
                    notif_email_ativo   = %(notif_email_ativo)s,
                    notif_fechada_ativa = %(notif_fechada_ativa)s,
                    notif_avencer_ativa = %(notif_avencer_ativa)s,
                    notif_vencida_ativa = %(notif_vencida_ativa)s,
                    notif_email_destino = %(notif_email_destino)s,
                    notif_telegram_ativo = %(notif_telegram_ativo)s
                WHERE id_usuario = %(id_usuario)s
            """
            params = {
                'id_usuario': parm_dict.get('id_usuario'),
                'notif_email_ativo': parm_dict.get('notif_email_ativo', True),
                'notif_fechada_ativa':
                    parm_dict.get('notif_fechada_ativa', True),
                'notif_avencer_ativa':
                    parm_dict.get('notif_avencer_ativa', True),
                'notif_vencida_ativa':
                    parm_dict.get('notif_vencida_ativa', True),
                'notif_email_destino':
                    parm_dict.get('notif_email_destino') or None,
                'notif_telegram_ativo':
                    parm_dict.get('notif_telegram_ativo', False),
            }
            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def set_telegram_link_token(self, id_usuario: int, token: str):
        """Grava o token temporário do deep link de vínculo."""
        rotina = 'set_telegram_link_token'

        try:
            cmdSql = """
                UPDATE usuario SET telegram_link_token = %(token)s
                WHERE id_usuario = %(id_usuario)s
            """
            self.execute_dml_command_parms(
                cmdSql, {'id_usuario': id_usuario, 'token': token})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def vincular_telegram_por_token(self, token: str, chat_id: str) -> int:
        """Acha o usuário pelo token do deep link, grava o chat_id, limpa o
        token e liga o canal. Retorna o id_usuario ou None."""
        rotina = 'vincular_telegram_por_token'

        try:
            query = """
                SELECT id_usuario FROM usuario
                WHERE telegram_link_token = %(token)s
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'token': token})
            linhas = self.convert_dataframe_to_dict(dataframe)
            if not linhas:
                return None

            id_usuario = linhas[0]['id_usuario']
            cmdSql = """
                UPDATE usuario SET
                    telegram_chat_id = %(chat_id)s,
                    telegram_link_token = NULL,
                    notif_telegram_ativo = TRUE
                WHERE id_usuario = %(id_usuario)s
            """
            self.execute_dml_command_parms(
                cmdSql, {'id_usuario': id_usuario, 'chat_id': str(chat_id)})
            return id_usuario

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def desvincular_telegram(self, id_usuario: int):
        """Remove o vínculo e desliga o canal."""
        rotina = 'desvincular_telegram'

        try:
            cmdSql = """
                UPDATE usuario SET
                    telegram_chat_id = NULL,
                    telegram_link_token = NULL,
                    notif_telegram_ativo = FALSE
                WHERE id_usuario = %(id_usuario)s
            """
            self.execute_dml_command_parms(
                cmdSql, {'id_usuario': id_usuario})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_primeiros_passos(self, id_usuario: int) -> dict:
        """Status do checklist calculado dos DADOS REAIS do usuário."""
        rotina = 'get_primeiros_passos'

        try:
            query = """
                SELECT
                  EXISTS (SELECT 1 FROM cartao ca
                          JOIN conta co ON co.id_conta = ca.id_conta
                          WHERE co.id_usuario = %(id)s)  AS tem_cartao,
                  EXISTS (SELECT 1 FROM compra cp
                          JOIN cartao ca ON ca.id_cartao = cp.id_cartao
                          JOIN conta co ON co.id_conta = ca.id_conta
                          WHERE co.id_usuario = %(id)s)  AS tem_compra,
                  EXISTS (SELECT 1 FROM orcamento o
                          WHERE o.id_usuario = %(id)s)   AS tem_orcamento,
                  EXISTS (SELECT 1 FROM usuario u
                          WHERE u.id_usuario = %(id)s
                            AND u.telegram_chat_id IS NOT NULL
                            AND u.notif_telegram_ativo)  AS telegram_ativo
            """
            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(),
                params={'id': id_usuario})
            return self.convert_dataframe_to_dict(dataframe)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def set_flag_usuario(self, id_usuario: int, campo: str, valor: bool):
        """Liga/desliga flags simples do usuário (whitelist de colunas)."""
        rotina = 'set_flag_usuario'

        if campo not in ('walkthrough_visto', 'checklist_oculto'):
            raise DAOException(__file__, rotina, f'Campo inválido: {campo}')

        try:
            cmdSql = f"""
                UPDATE usuario SET {campo} = %(valor)s
                WHERE id_usuario = %(id_usuario)s
            """
            self.execute_dml_command_parms(
                cmdSql, {'id_usuario': id_usuario, 'valor': valor})

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def insert_categorias_padrao(self, id_usuario: int, categorias: list):
        """Insere as categorias padrão do usuário novo NA MESMA conexão do
        insert_usuario (mesma transação) — não faz commit; o facade dá um
        commit só, pra usuário + categorias entrarem juntos ou nada entrar."""
        rotina = 'insert_categorias_padrao'

        try:
            cmdSql = """
                INSERT INTO categoria (id_usuario, dsc_categoria,
                    id_tipo_categoria)
                VALUES (%(id_usuario)s, %(dsc_categoria)s,
                    %(id_tipo_categoria)s)
            """
            for (dsc, id_tipo) in categorias:
                self.execute_dml_command_parms(cmdSql, {
                    "id_usuario": id_usuario,
                    "dsc_categoria": dsc,
                    "id_tipo_categoria": id_tipo,
                })

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def delete_usuario(self, id_usuario: int):
        rotina = 'delete_usuario'

        try:
            cmdSql = """
                DELETE FROM usuario
                WHERE id_usuario = %(id_usuario)s
            """

            params = {'id_usuario': id_usuario}

            self.execute_dml_command_parms(cmdSql, params)

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
