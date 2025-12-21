from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiUserFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiUserDAO()

    def obter_usuario(self, ch_rede=None) -> dict:
        rotina = 'obter_usuario'

        try:
            if ch_rede is not None:
                ch_rede = ch_rede.strip()
            user = self.dao.get_user(ch_rede=ch_rede)
            return convert_unique_dic_to_arrayDict(user)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_usuario(self, parm_dict: dict):
        rotina = 'criar_usuario'

        try:
            parm_dict['ch_rede'] = parm_dict['ch_rede'].strip().upper()

            usuario_existente = self.dao.get_user(ch_rede=parm_dict['ch_rede'])
            if usuario_existente:
                raise FacadeException(
                    __file__, rotina, 'Esse usuário já existe')

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

    def deletar_usuario(self, id_usuario: int, ch_rede: str):
        rotina = 'deletar_usuario'

        try:
            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            ch_rede = ch_rede.strip().upper()

            # Verificar se usuário existe
            usuario = self.dao.get_user_by_id(id_usuario=id_usuario)
            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado')

            self.dao.delete_usuario(id_usuario, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
