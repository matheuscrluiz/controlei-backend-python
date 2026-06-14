from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_cartao_dao import ControleiCartaoDAO

FUNCOES_VALIDAS = ('credito', 'debito', 'multiplo')
FUNCOES_COM_CREDITO = ('credito', 'multiplo')


class ControleiCartaoFacade():

    def __init__(self):
        """construtor da classe ControleiCartaoFacade"""
        self.dao = ControleiCartaoDAO()

    def obter_cartao(self, id_cartao=None, id_conta=None,
                     id_usuario=None) -> dict:
        rotina = 'obter_cartao'

        try:
            cartao = self.dao.get_cartao(
                id_cartao=id_cartao,
                id_conta=id_conta,
                id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(cartao)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def _validar(self, parm_dict: dict, rotina: str):
        """Validações comuns a criar/atualizar."""
        apelido = (parm_dict.get('apelido') or '').strip()
        funcao = (parm_dict.get('funcao') or '').strip().lower()

        if not apelido:
            raise FacadeException(
                __file__, rotina, 'Apelido do cartão é obrigatório')

        if funcao not in FUNCOES_VALIDAS:
            raise FacadeException(
                __file__, rotina,
                'Função inválida (use: credito, debito ou multiplo)')

        # Crédito precisa de fechamento e vencimento — sem isso o ciclo da
        # fatura não funciona (não dá pra saber em qual fatura a compra cai).
        if funcao in FUNCOES_COM_CREDITO:
            if not parm_dict.get('dia_fechamento') \
                    or not parm_dict.get('dia_vencimento'):
                raise FacadeException(
                    __file__, rotina,
                    'Cartão de crédito precisa de dia de fechamento e de '
                    'vencimento')

        return apelido, funcao

    def criar_cartao(self, parm_dict: dict):
        rotina = 'criar_cartao'

        try:
            id_conta = parm_dict.get('id_conta')
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'ID da conta é obrigatório')

            apelido, funcao = self._validar(parm_dict, rotina)

            parms = {
                'id_conta': id_conta,
                'id_cartao_pai': parm_dict.get('id_cartao_pai'),
                'apelido': apelido,
                'funcao': funcao,
                'bandeira': parm_dict.get('bandeira'),
                'ultimos4': parm_dict.get('ultimos4'),
                'limite': parm_dict.get('limite'),
                'dia_fechamento': parm_dict.get('dia_fechamento'),
                'dia_vencimento': parm_dict.get('dia_vencimento'),
            }

            id_cartao = self.dao.insert_cartao(parms)
            self.dao.database_commit()

            return id_cartao

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_cartao(self, parm_dict: dict):
        rotina = 'atualizar_cartao'

        try:
            id_cartao = parm_dict.get('id_cartao')
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')

            cartao = self.dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')

            apelido, funcao = self._validar(parm_dict, rotina)

            parms = {
                'id_cartao': id_cartao,
                'id_cartao_pai': parm_dict.get('id_cartao_pai'),
                'apelido': apelido,
                'funcao': funcao,
                'bandeira': parm_dict.get('bandeira'),
                'ultimos4': parm_dict.get('ultimos4'),
                'limite': parm_dict.get('limite'),
                'dia_fechamento': parm_dict.get('dia_fechamento'),
                'dia_vencimento': parm_dict.get('dia_vencimento'),
            }

            self.dao.update_cartao(parms)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_cartao(self, id_cartao: int):
        rotina = 'deletar_cartao'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')

            cartao = self.dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')

            self.dao.delete_cartao(id_cartao)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
