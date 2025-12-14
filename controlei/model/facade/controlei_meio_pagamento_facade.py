from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_meio_pagamento_dao import ControleiMeioPagamentoDAO


class ControleiMeioPagamentoFacade():

    def __init__(self):
        """construtor da classe ControleiUserFacade"""
        self.dao = ControleiMeioPagamentoDAO()

    def obter_meio_pagamento(self, id_meio_pagamento=None) -> dict:
        rotina = 'obter_meio_pagamento'

        try:

            meio_pagamento = self.dao.get_meio_pagamento(
                id_meio_pagamento=id_meio_pagamento)
            return convert_unique_dic_to_arrayDict(meio_pagamento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_meio_pagamento(self, parm_dict: dict):
        rotina = 'criar_meio_pagamento'

        try:

            id_meio_pagamento = self.dao.insert_meio_pagamento(parm_dict)
            self.dao.database_commit()

            return id_meio_pagamento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_meio_pagamento(self, parm_dict: dict):
        rotina = 'atualizar_meio_pagamento'

        try:
            if not parm_dict['id_meio_pagamento']:
                raise FacadeException(
                    __file__, rotina, 'ID do meio de pagamento é obrigatório')

            meio_pagamento = self.dao.get_meio_pagamento(
                id_meio_pagamento=parm_dict['id_meio_pagamento'])
            if not meio_pagamento:
                raise FacadeException(
                    __file__, rotina, 'Meio de pagamento não encontrado')

            self.dao.update_meio_pagamento(parm_dict)
            self.dao.database_commit()
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
