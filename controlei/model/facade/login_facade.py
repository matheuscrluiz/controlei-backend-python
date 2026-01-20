from ...util.exceptions import FacadeException
from ..dao.login_dao import LoginDAO


class LoginFacade():

    def __init__(self):
        """Construtor da classe LoginFacade"""
        self.dao = LoginDAO()

    def login(self, ch_rede: str, senha: str) -> dict:
        """
        Realiza o login de um usuário

        Args:
            ch_rede (str): Chave de rede do usuário
            senha (str): Senha do usuário

        Returns:
            dict: Dados do usuário autenticado

        Raises:
            FacadeException: Se as credenciais forem inválidas
        """
        rotina = 'login'

        try:
            # Validar entrada
            if not ch_rede or not ch_rede.strip():
                raise FacadeException(
                    __file__, rotina, 'ch_rede é obrigatória')

            if not senha or not senha.strip():
                raise FacadeException(
                    __file__, rotina, 'senha é obrigatória')

            ch_rede = ch_rede.strip().upper()

            # Autenticar usuário
            user = self.dao.authenticate_user(ch_rede, senha)

            if not user:
                raise FacadeException(
                    __file__, rotina, 'Usuário ou senha inválidos')

            return user

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
