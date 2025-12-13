from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiUserFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiUserDAO()

    def obter_usuario(self, nome=None) -> dict:
        rotina = 'obter_usuario'

        try:
            if nome is not None:
                nome = nome.strip()
            user = self.dao.get_user(nome=nome)
            return convert_unique_dic_to_arrayDict(user)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_usuario(self, parm_dict: dict):
        rotina = 'criar_usuario'

        try:
            email = parm_dict.get('email')
            nome = parm_dict.get('nome')

            if not email or not nome:
                raise FacadeException(
                    __file__, rotina, 'Email e nome são obrigatórios')

            # Verificar se email já existe
            usuario_existente = self.dao.get_user_by_email(email=email)
            if usuario_existente:
                raise FacadeException(
                    __file__, rotina, 'Esse e-mail já existe')

            # Inserir novo usuário
            user_id = self.dao.insert_usuario(parm_dict)
            self.dao.database_commit()

            return user_id

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_usuario(self, parm_dict: dict):
        rotina = 'atualizar_usuario'

        try:
            if not parm_dict['id_usuario']:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            # Verificar se usuário existe
            usuario = self.dao.get_user_by_id(
                id_usuario=parm_dict['id_usuario'])
            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado')

            self.dao.update_usuario(parm_dict)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_usuario(self, id_usuario: int):
        rotina = 'deletar_usuario'

        try:
            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            # Verificar se usuário existe
            usuario = self.dao.get_user_by_id(id_usuario=id_usuario)
            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado')

            self.dao.delete_usuario(id_usuario)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
