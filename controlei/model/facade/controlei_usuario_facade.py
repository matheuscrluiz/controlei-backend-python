from werkzeug.security import generate_password_hash
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiUserFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiUserDAO()

    def obter_usuario(self, id_usuario=None, email=None) -> dict:
        rotina = 'obter_usuario'

        try:
            if email is not None:
                email = email.strip().lower()

            user = self.dao.get_user(id_usuario=id_usuario, email=email)
            return convert_unique_dic_to_arrayDict(user)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_usuario(self, parm_dict: dict):
        rotina = 'criar_usuario'

        try:
            nome = (parm_dict.get('nome') or '').strip()
            email = (parm_dict.get('email') or '').strip().lower()
            senha = parm_dict.get('senha') or ''

            if not nome:
                raise FacadeException(__file__, rotina, 'Nome é obrigatório')
            if not email:
                raise FacadeException(__file__, rotina, 'E-mail é obrigatório')
            if not senha:
                raise FacadeException(__file__, rotina, 'Senha é obrigatória')

            if self.dao.get_user(email=email):
                raise FacadeException(
                    __file__, rotina, 'Esse e-mail já está cadastrado')

            parms = {
                'nome': nome,
                'email': email,
                'senha_hash': generate_password_hash(senha)
            }

            user_id = self.dao.insert_usuario(parms)
            self.dao.database_commit()

            return user_id

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_usuario(self, parm_dict: dict):
        rotina = 'atualizar_usuario'

        try:
            id_usuario = parm_dict.get('id_usuario')
            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            usuario = self.dao.get_user(id_usuario=id_usuario)
            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado')

            nome = (parm_dict.get('nome') or '').strip()
            email = (parm_dict.get('email') or '').strip().lower()

            if not nome:
                raise FacadeException(__file__, rotina, 'Nome é obrigatório')
            if not email:
                raise FacadeException(__file__, rotina, 'E-mail é obrigatório')

            # E-mail tem que ser único — só barra se for de OUTRO usuário.
            existente = self.dao.get_user(email=email)
            if existente and int(existente[
                    0]['id_usuario']) != int(id_usuario):
                raise FacadeException(
                    __file__, rotina, 'Esse e-mail já está em uso')

            self.dao.update_usuario({
                'id_usuario': id_usuario,
                'nome': nome,
                'email': email
            })

            # Senha é opcional no update; se veio, re-hasheia.
            senha = parm_dict.get('senha')
            if senha:
                self.dao.update_senha(
                    id_usuario, generate_password_hash(senha))

            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_usuario(self, id_usuario: int):
        rotina = 'deletar_usuario'

        try:
            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            usuario = self.dao.get_user(id_usuario=id_usuario)
            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado')

            self.dao.delete_usuario(id_usuario)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
