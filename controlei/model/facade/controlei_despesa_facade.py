from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_despesa_dao import ControleiDespesaDAO
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO
from ..dao.controlei_usuario_dao import ControleiUserDAO


class ControleiDespesaFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiDespesaDAO()
        self.cat_dao = ControleiCategoriaDAO()
        self.user_dao = ControleiUserDAO()

    def obter_despesa(
        self,
        id_despesa=None,
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

            receita = self.dao.get_expenses(
                id_despesa=id_despesa,
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

    def criar_despesa(self, parm_dict: dict):
        rotina = 'criar_despesa'

        try:
            obtem_categoria = convert_unique_dic_to_arrayDict(
                self.cat_dao.get_category(
                    id_categoria=parm_dict['id_categoria']
                ))
            print('obtem_categoria: ', obtem_categoria)

            if not obtem_categoria:
                raise FacadeException(
                    __file__,
                    rotina,
                    "Categoria não encontrada!"
                )

            if obtem_categoria[0][
                    'codigo_tipo_categoria'] != 'Despesa':
                raise FacadeException(
                    __file__,
                    rotina,
                    "A categoria deve ser do tipo despesa"
                )

            if parm_dict['valor_total'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da despesa não pode ser menor que zero"
                )

            id_despesa = self.dao.insert_expense(parm_dict)
            self.dao.database_commit()

            return id_despesa

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_despesa(self, parm_dict: dict):
        rotina = 'atualizar_despesa'

        try:
            if not parm_dict.get('id_despesa'):
                raise FacadeException(
                    __file__, rotina, 'ID da despesa é obrigatório'
                )

            despesa = self.dao.get_expenses(
                id_despesa=parm_dict['id_despesa'],
                ch_rede=parm_dict['ch_rede'])
            if not despesa:
                raise FacadeException(
                    __file__, rotina, 'despesa não encontrada'
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

            if parm_dict['valor_total'] < 0:
                raise FacadeException(
                    __file__,
                    rotina,
                    "O valor da receita não pode ser menor que zero"
                )

            self.dao.update_expense(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_despesa(
            self,
            id_despesa: int,
            ch_rede: str
    ):
        rotina = 'apagar_despesa'

        try:
            if not id_despesa:
                raise FacadeException(
                    __file__, rotina, 'ID da despesa é obrigatório'
                )

            despesa = self.dao.get_expenses(
                id_despesa=id_despesa,
                ch_rede=ch_rede)
            if not despesa:
                raise FacadeException(
                    __file__, rotina, 'despesa não encontrada'
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
                    'Você não tem permissão para deletar esta despesa'
                )

            self.dao.delete_expense(id_despesa, ch_rede)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
