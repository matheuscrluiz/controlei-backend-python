import pandas as pd
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base


class LoginDAO(base.DAOBase):

    def __init__(self):
        super().__init__()

    def authenticate_user(self, ch_rede: str, senha: str) -> dict:
        """
        Autentica um usuário verificando ch_rede e senha no banco de dados

        Args:
            ch_rede (str): Chave de rede do usuário
            senha (str): Senha do usuário

        Returns:
            dict: Dados do usuário autenticado ou None se não encontrado
        """
        rotina = 'authenticate_user'

        try:
            query = """
                select id_usuario, ch_rede, nome, email, matricula, cpf
                from usuario
                where ch_rede = %(ch_rede)s
                and senha = %(senha)s
            """

            params_oracle = {
                'ch_rede': ch_rede,
                'senha': senha
            }

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            if dataframe.empty:
                return None

            return dataframe.to_dict(orient='records')[0]

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)

    def get_user_by_ch_rede(self, ch_rede: str) -> dict:
        """
        Obtém um usuário pela ch_rede sem validar senha

        Args:
            ch_rede (str): Chave de rede do usuário

        Returns:
            dict: Dados do usuário ou None se não encontrado
        """
        rotina = 'get_user_by_ch_rede'

        try:
            query = """
                select id_usuario, ch_rede, nome, email, matricula, cpf
                from usuario
                where ch_rede = %(ch_rede)s
            """

            params_oracle = {'ch_rede': ch_rede}

            dataframe = pd.read_sql(
                sql=query, con=self.get_connection(), params=params_oracle)

            if dataframe.empty:
                return None

            return dataframe.to_dict(orient='records')[0]

        except DAOException as erro:
            raise DAOException(__file__, rotina, erro)
