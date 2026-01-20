from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_meta_movimentacao_dao import ControleiMetaMovimentacaoDAO
from ..dao.controlei_meta_dao import ControleiMetaDAO


class ControleiMetaMovimentacaoFacade():

    def __init__(self):
        """construtor da classe ControleiMetaMovimentacaoFacade"""
        self.dao = ControleiMetaMovimentacaoDAO()
        self.meta_dao = ControleiMetaDAO()

    def obter_movimentacao(
        self,
        ch_rede: str,
        id_movimentacao: int = None,
        id_meta: int = None,
    ) -> dict:
        rotina = 'obter_movimentacao'

        try:

            ch_rede = ch_rede.upper()
            movimentacao = self.dao.get_movimentacoes(
                ch_rede=ch_rede,
                id_movimentacao=id_movimentacao,
                id_meta=id_meta,
            )
            return convert_unique_dic_to_arrayDict(movimentacao)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_movimentacao(self, parm_dict: dict):
        rotina = 'criar_movimentacao'

        try:
            if not parm_dict.get('id_meta'):
                raise FacadeException(
                    __file__,
                    rotina,
                    "ID da meta é obrigatório"
                )

            if parm_dict['valor'] <= 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da movimentação deve ser maior que zero"
                )

            if not parm_dict.get('data_movimentacao'):
                raise FacadeException(
                    __file__,
                    rotina,
                    "Data da movimentação é obrigatória"
                )

            if not parm_dict.get('origem'):
                # raise FacadeException(
                #     __file__,
                #     rotina,
                #     "Origem da movimentação é obrigatória"
                # )
                parm_dict['origem'] = "MANUAL"

            id_movimentacao = self.dao.insert_movimentacao(parm_dict)
            self.dao.database_commit()

            return id_movimentacao

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_movimentacao(self, parm_dict: dict):
        rotina = 'atualizar_movimentacao'

        try:
            if not parm_dict.get('id_movimentacao'):
                raise FacadeException(
                    __file__, rotina, 'ID da movimentação é obrigatório'
                )

            movimentacao = self.dao.get_movimentacoes(
                id_movimentacao=parm_dict['id_movimentacao'])

            if not movimentacao:
                raise FacadeException(
                    __file__, rotina, 'Movimentação não encontrada'
                )

            if parm_dict.get('valor') and parm_dict['valor'] <= 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da movimentação deve ser maior que zero"
                )

            self.dao.update_movimentacao(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_movimentacao(
            self,
            id_movimentacao: int
    ):
        rotina = 'apagar_movimentacao'

        try:
            if not id_movimentacao:
                raise FacadeException(
                    __file__, rotina, 'ID da movimentação é obrigatório'
                )

            movimentacao = self.dao.get_movimentacoes(
                id_movimentacao=id_movimentacao)

            if not movimentacao:
                raise FacadeException(
                    __file__, rotina, 'Movimentação não encontrada'
                )

            self.dao.delete_movimentacao(id_movimentacao)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
