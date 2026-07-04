from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_orcamento_dao import ControleiOrcamentoDAO


def _norm_competencia(valor):
    """Normaliza a competência para o 1º dia do mês (YYYY-MM-01) ou None."""
    if not valor:
        return None
    s = str(valor).strip()
    if not s:
        return None
    s = s.split('T')[0].split(' ')[0]          # tolera ISO completo
    partes = s.split('-')
    if len(partes) >= 2:
        return f"{partes[0]}-{partes[1]}-01"
    return s


class ControleiOrcamentoFacade():

    def __init__(self):
        self.dao = ControleiOrcamentoDAO()

    def obter_orcamento(
            self,
            id_orcamento=None,
            id_usuario=None,
            id_categoria=None) -> dict:
        rotina = 'obter_orcamento'

        try:
            orcamento = self.dao.get_orcamento(
                id_orcamento=id_orcamento,
                id_usuario=id_usuario,
                id_categoria=id_categoria)
            return convert_unique_dic_to_arrayDict(orcamento)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_padrao(self, id_usuario) -> dict:
        rotina = 'obter_padrao'

        try:
            return convert_unique_dic_to_arrayDict(
                self.dao.get_padrao(id_usuario=id_usuario))

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_efetivo(self, id_usuario, competencia) -> dict:
        """Teto efetivo por categoria no mês (override do mês OU padrão)."""
        rotina = 'obter_efetivo'

        try:
            comp = _norm_competencia(competencia)
            if not comp:
                raise FacadeException(
                    __file__, rotina, 'Competência é obrigatória')
            return convert_unique_dic_to_arrayDict(
                self.dao.get_efetivo(id_usuario=id_usuario, competencia=comp))

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_mes(self, id_usuario, competencia) -> dict:
        """Apenas os overrides (tetos específicos) de um mês."""
        rotina = 'obter_mes'

        try:
            comp = _norm_competencia(competencia)
            return convert_unique_dic_to_arrayDict(
                self.dao.get_override(
                    id_usuario=id_usuario, competencia=comp))

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_orcamento(self, parm_dict: dict):
        """Cria um teto. Sem competência = padrão; com competência = override
        do mês. Bloqueia duplicado no respectivo escopo."""
        rotina = 'criar_orcamento'

        try:
            id_usuario = parm_dict.get('id_usuario')
            id_categoria = parm_dict.get('id_categoria')
            valor_teto = parm_dict.get('valor_teto')
            competencia = _norm_competencia(parm_dict.get('competencia'))

            if not id_usuario:
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')
            if not id_categoria:
                raise FacadeException(
                    __file__, rotina, 'Categoria é obrigatória')
            if valor_teto is None or float(valor_teto) <= 0:
                raise FacadeException(
                    __file__, rotina, 'O teto deve ser maior que zero')

            if competencia:
                existente = self.dao.get_override(
                    id_usuario=id_usuario, competencia=competencia,
                    id_categoria=id_categoria)
                msg_dup = 'Já existe um ajuste desta categoria neste mês'
            else:
                existente = self.dao.get_padrao(
                    id_usuario=id_usuario, id_categoria=id_categoria)
                msg_dup = 'Já existe um teto padrão para esta categoria'

            if existente:
                raise FacadeException(__file__, rotina, msg_dup)

            id_orcamento = self.dao.insert_orcamento({
                'id_usuario': id_usuario,
                'id_categoria': id_categoria,
                'valor_teto': valor_teto,
                'competencia': competencia,
            })
            self.dao.database_commit()

            return id_orcamento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_orcamento(self, parm_dict: dict):
        rotina = 'atualizar_orcamento'

        try:
            if not parm_dict.get('id_orcamento'):
                raise FacadeException(
                    __file__, rotina, 'ID do orçamento é obrigatório')

            valor_teto = parm_dict.get('valor_teto')
            if valor_teto is None or float(valor_teto) <= 0:
                raise FacadeException(
                    __file__, rotina, 'O teto deve ser maior que zero')

            orcamento = self.dao.get_orcamento(
                id_orcamento=parm_dict['id_orcamento'])
            if not orcamento:
                raise FacadeException(
                    __file__, rotina, 'Orçamento não encontrado')

            self.dao.update_orcamento(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def apagar_orcamento(self, id_orcamento: int):
        rotina = 'apagar_orcamento'

        try:
            if not id_orcamento:
                raise FacadeException(
                    __file__, rotina, 'ID do orçamento é obrigatório')

            orcamento = self.dao.get_orcamento(id_orcamento=id_orcamento)
            if not orcamento:
                raise FacadeException(
                    __file__, rotina, 'Orçamento não encontrado')

            self.dao.delete_orcamento(id_orcamento)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
