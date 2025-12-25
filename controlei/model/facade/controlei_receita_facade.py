from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_receita_dao import ControleiReceitaDAO
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiReceitaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiReceitaDAO()
        self.cat_dao = ControleiCategoriaDAO()
        self.user_dao = ControleiUserDAO()

    def obter_receita(
        self,
        id_receita=None,
        ch_rede=None,
        tipo_filtro=None,
        mes_inicial=None,
        mes_final=None,
        ano=None,
        data_dia=None
    ) -> dict:
        rotina = 'obter_receita'

        try:

            mes_inicial = mes_inicial[3:]
            mes_final = mes_final[3:]
            ano = ano[6:]

            receita = self.dao.get_income(
                id_receita=id_receita,
                ch_rede=ch_rede,
                tipo_filtro=tipo_filtro,
                mes_inicial=mes_inicial,
                mes_final=mes_final,
                ano=ano,
                data_dia=data_dia
            )
            return convert_unique_dic_to_arrayDict(receita)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_receita(self, parm_dict: dict):
        rotina = 'criar_receita'

        try:
            obtem_categoria = convert_unique_dic_to_arrayDict(
                self.cat_dao.get_category(
                    id_categoria=parm_dict['id_categoria']
                ))

            if not obtem_categoria:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Categoria não encontrada!"
                )

            if obtem_categoria[0][
                    'codigo_tipo_categoria'] != 'Receita':
                raise FacadeException(
                    __file__,
                    rotina,
                    "A categoria deve ser do tipo receita"
                )

            if parm_dict['valor'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da receita não pode ser menor que zero"
                )

            id_receita = self.dao.insert_income(parm_dict)
            self.dao.database_commit()

            return id_receita

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_receita(self, parm_dict: dict):
        rotina = 'atualizar_receita'

        try:
            if not parm_dict.get('id_receita'):
                raise FacadeException(
                    __file__, rotina, 'ID da receita é obrigatório'
                )

            receita = self.dao.get_income(
                id_receita=parm_dict['id_receita'],
                ch_rede=parm_dict['ch_rede'])
            if not receita:
                raise FacadeException(
                    __file__, rotina, 'Receita não encontrada'
                )

            obtem_categoria = convert_unique_dic_to_arrayDict(
                self.cat_dao.get_category(
                    id_categoria=parm_dict['id_categoria']
                )
            )

            if not obtem_categoria:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Categoria não encontrada!"
                )

            if parm_dict['valor'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da receita não pode ser menor que zero"
                )

            self.dao.update_income(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_receita(
            self,
            id_receita: int,
            ch_rede: str
    ):
        rotina = 'apagar_receita'

        try:
            if not id_receita:
                raise FacadeException(
                    __file__, rotina, 'ID da receita é obrigatório'
                )

            receita = self.dao.get_income(
                id_receita=id_receita,
                ch_rede=ch_rede)
            if not receita:
                raise FacadeException(
                    __file__, rotina, 'Receita não encontrada'
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
                    'Você não tem permissão para deletar esta receita'
                )

            self.dao.delete_income(id_receita, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
