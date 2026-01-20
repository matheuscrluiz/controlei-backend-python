from ...util.exceptions import FacadeException, NotFoundException
from ...util.constants import OBJETO_EXISTENTE
from ..dao.area_dao import AreaDAO as area_dao


class AreaFacade():

    def __init__(self):
        """construtor da classe AreaFacade"""

    # --------------------------------------------------------------------------
    #
    # --------------------------------------------------------------------------
    def obter_area(self):

        rotina = 'obter_area'

        try:

            area = area_dao().get_area()

            return area

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_area(self, parm_data: dict) -> int:
        rotina = 'criar_area'

        try:

            area = area_dao()
            row_uk = area.get_area()

            if row_uk:
                raise FacadeException(__file__, rotina, OBJETO_EXISTENTE)

            print(parm_data)
            id = area.add_area(parm_data)
            print('id: ', id)
            area.database_commit()

            return id

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_area(self, parm_data: dict):
        rotina = 'apagar_area'

        try:

            area = area_dao()

            area.remove_area(parm_data)

            area.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def alterar_area(self, parm_data: dict):
        rotina = 'alterar_area'

        try:

            # eliminando espaços em branco laterais
            parm_data["nom_area"] = parm_data["nom_area"].strip()

            area = area_dao()

            area.update_area(parm_data)

            area.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
