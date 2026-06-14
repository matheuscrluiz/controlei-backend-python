from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_conta_dao import ControleiContaDAO


class ControleiContaFacade():

    def __init__(self):
        """construtor da classe ControleiContaFacade"""
        self.dao = ControleiContaDAO()

    def obter_conta(self, id_conta=None, id_usuario=None) -> dict:
        rotina = 'obter_conta'

        try:
            conta = self.dao.get_conta(
                id_conta=id_conta, id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(conta)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_conta(self, parm_dict: dict):
        rotina = 'criar_conta'

        try:
            id_usuario = parm_dict.get('id_usuario')
            apelido = (parm_dict.get('apelido') or '').strip()

            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')
            if not apelido:
                raise FacadeException(
                    __file__, rotina, 'Apelido da conta é obrigatório')

            parms = {
                'id_usuario': id_usuario,
                'id_instituicao': parm_dict.get('id_instituicao'),
                'apelido': apelido,
                'tipo': (parm_dict.get('tipo') or 'corrente').strip(),
            }

            id_conta = self.dao.insert_conta(parms)
            self.dao.database_commit()

            return id_conta

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_conta(self, parm_dict: dict):
        rotina = 'atualizar_conta'

        try:
            id_conta = parm_dict.get('id_conta')
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'ID da conta é obrigatório')

            conta = self.dao.get_conta(id_conta=id_conta)
            if not conta:
                raise FacadeException(
                    __file__, rotina, 'Conta não encontrada')

            apelido = (parm_dict.get('apelido') or '').strip()
            if not apelido:
                raise FacadeException(
                    __file__, rotina, 'Apelido da conta é obrigatório')

            parms = {
                'id_conta': id_conta,
                'id_instituicao': parm_dict.get('id_instituicao'),
                'apelido': apelido,
                'tipo': (parm_dict.get('tipo') or 'corrente').strip(),
            }

            self.dao.update_conta(parms)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_conta(self, id_conta: int):
        rotina = 'deletar_conta'

        try:
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'ID da conta é obrigatório')

            conta = self.dao.get_conta(id_conta=id_conta)
            if not conta:
                raise FacadeException(
                    __file__, rotina, 'Conta não encontrada')

            self.dao.delete_conta(id_conta)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
