from werkzeug.security import check_password_hash
from ...util.controlei_jwt import gerar_token
from ...util.exceptions import FacadeException
from ..dao.controlei_usuario_dao import ControleiUserDAO
from ..dao.controlei_conta_dao import ControleiContaDAO


class LoginFacade():

    def __init__(self):
        """Construtor da classe LoginFacade"""
        # Reusa o DAO de usuário: autenticar é
        #  buscar credenciais + conferir senha.
        self.dao = ControleiUserDAO()
        # Para resolver o onboarding já no login (usuário tem conta?).
        self.conta_dao = ControleiContaDAO()

    def login(self, email: str, senha: str) -> dict:
        """
        Realiza o login de um usuário.

        Args:
            email (str): E-mail do usuário
            senha (str): Senha em texto puro (conferida contra o hash)

        Returns:
            dict: Dados do usuário autenticado (sem o hash)

        Raises:
            FacadeException: Se as credenciais forem inválidas
        """
        rotina = 'login'

        try:
            if not email or not email.strip():
                raise FacadeException(__file__, rotina, 'E-mail é obrigatório')

            if not senha or not senha.strip():
                raise FacadeException(__file__, rotina, 'Senha é obrigatória')

            email = email.strip().lower()

            credenciais = self.dao.get_credenciais_by_email(email)

            # Mensagem genérica de propósito:
            # não revela se foi o e-mail ou a senha.
            if not credenciais:
                raise FacadeException(
                    __file__, rotina, 'Usuário ou senha inválidos')

            cred = credenciais[0]

            if not check_password_hash(cred.get('senha_hash') or '', senha):
                raise FacadeException(
                    __file__, rotina, 'Usuário ou senha inválidos')

            # Resolve o onboarding aqui: tem ao menos uma conta?
            contas = self.conta_dao.get_conta(id_usuario=cred['id_usuario'])

            # Devolve só o necessário — o hash nunca sai daqui.
            return {
                'id_usuario': cred['id_usuario'],
                'nome': cred['nome'],
                'email': cred['email'],
                'onboarded': bool(contas),
                # Token de sessão (24h): o front envia em
                # Authorization: Bearer <token> em toda chamada.
                'token': gerar_token(cred['id_usuario'])
            }

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
