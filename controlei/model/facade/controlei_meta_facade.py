from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_meta_dao import ControleiMetaDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiMetaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiMetaDAO()
        self.user_dao = ControleiUserDAO()

    def obter_meta(
        self,
        id_meta=None,
        ch_rede=None,
    ) -> dict:
        rotina = 'obter_meta'

        try:

            ch_rede = ch_rede.upper()

            meta = self.dao.get_goals(
                id_meta=id_meta,
                ch_rede=ch_rede,
            )
            return convert_unique_dic_to_arrayDict(meta)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_meta(self, parm_dict: dict):
        rotina = 'criar_meta'

        try:
            parm_dict['ch_rede'] = parm_dict['ch_rede'].upper()

            if parm_dict['valor_meta'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da meta não pode ser menor que zero"
                )

            id_meta = self.dao.insert_goals(parm_dict)
            self.dao.database_commit()

            return id_meta

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_meta(self, parm_dict: dict):
        rotina = 'atualizar_meta'

        try:
            if not parm_dict.get('id_meta'):
                raise FacadeException(
                    __file__, rotina, 'ID da meta é obrigatório'
                )

            meta = self.dao.get_goals(
                id_meta=parm_dict['id_meta'],
                ch_rede=parm_dict['ch_rede'])
            if not meta:
                raise FacadeException(
                    __file__, rotina, 'meta não encontrada'
                )

            if parm_dict['valor_meta'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da meta não pode ser menor que zero"
                )

            prioridade_antiga = meta[0]['prioridade']
            prioridade_nova = parm_dict['prioridade']

            if prioridade_antiga != prioridade_nova:
                self.reordenar_prioridades(
                    parm_dict['ch_rede'],
                    parm_dict['id_meta'],
                    prioridade_antiga,
                    prioridade_nova
                )

            self.dao.update_goals(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_meta(
            self,
            id_meta: int,
            ch_rede: str
    ):
        rotina = 'apagar_meta'

        try:
            if not id_meta:
                raise FacadeException(
                    __file__, rotina, 'ID da meta é obrigatório'
                )

            meta = self.dao.get_goals(
                id_meta=id_meta,
                ch_rede=ch_rede)
            if not meta:
                raise FacadeException(
                    __file__, rotina, 'meta não encontrada'
                )

            usuario = self.user_dao.get_user(
                ch_rede=ch_rede)

            if not usuario:
                raise FacadeException(
                    __file__, rotina, 'Usuário não encontrado'
                )
            if usuario[0]['ch_rede'] != ch_rede:
                raise FacadeException(
                    __file__,
                    rotina,
                    'Você não tem permissão para deletar esta meta'
                )

            self.dao.delete_goals(id_meta, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def reordenar_prioridades(
        self,
        ch_rede: str,
        id_meta: int,
        prioridade_antiga: int,
        prioridade_nova: int
    ):
        rotina = 'reordenar_prioridades'
        try:
            if prioridade_nova < prioridade_antiga:
                self.dao.shift_prioridades_down(
                    ch_rede,
                    prioridade_nova,
                    prioridade_antiga - 1
                )

            elif prioridade_nova > prioridade_antiga:
                self.dao.shift_prioridades_up(
                    ch_rede,
                    prioridade_antiga + 1,
                    prioridade_nova
                )
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_relatorio_saldo_mensal(self, ch_rede: str) -> dict:
        rotina = 'obter_relatorio_saldo_mensal'

        try:
            ch_rede = ch_rede.upper()

            relatorio = self.dao.get_monthly_balance_report(ch_rede=ch_rede)
            return convert_unique_dic_to_arrayDict(relatorio)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
