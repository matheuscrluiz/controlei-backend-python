from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_conta_dao import ControleiContaDAO
from ..dao.controlei_categoria_dao import ControleiCategoriaDAO
from ..dao.controlei_derivados_dao import ControleiDerivadosDAO
from datetime import date
from .controlei_lancamento_facade import ControleiLancamentoFacade


class ControleiContaFacade():

    def __init__(self):
        """construtor da classe ControleiContaFacade"""
        self.dao = ControleiContaDAO()
        self.lancamento_facade = ControleiLancamentoFacade()

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

            # Saldo de abertura (só se diferente de zero).
            # Mesma regra do onboarding: o saldo inicial não é coluna da
            # conta, é um lançamento de natureza='ajuste'.
            saldo = parm_dict.get('saldo_abertura')
            if saldo is not None and Decimal(str(saldo)) != 0:
                self.lancamento_facade.criar_lancamento({
                    'id_conta': id_conta,
                    'natureza': 'ajuste',
                    'valor': saldo,
                    'descricao': 'Saldo de abertura',
                    'status': 'efetivado',
                })

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

    # ------------------------------------------------------------------
    # CONCILIAÇÃO DE SALDO
    # ------------------------------------------------------------------
    def conciliar_saldo(self, id_conta: int,
                        saldo_informado, id_usuario: int) -> dict:
        """
        O usuário informa o saldo que o BANCO mostra. Calculamos a diferença
        contra o saldo do Controlei (soma dos lançamentos) e registramos um
        lançamento que a zera:
          * conta `rende` e diferença > 0 → receita "Rendimento";
          * senão → "Ajuste de conciliação" (receita ou despesa pelo sinal),
            sinalizando algo não registrado (tarifa, pix esquecido...).
        Diferença < R$ 0,01 → nada a fazer. O saldo passa a bater exatamente.
        """
        rotina = 'conciliar_saldo'
        try:
            saldo_informado = float(saldo_informado)
            atual = convert_unique_dic_to_arrayDict(
                ControleiDerivadosDAO().get_saldo_conta(id_conta))
            saldo_atual = float((atual[0] if atual else {}).get('saldo') or 0)
            diff = round(saldo_informado - saldo_atual, 2)

            conta = convert_unique_dic_to_arrayDict(
                self.dao.get_conta(id_conta=id_conta))
            conta = conta[0] if conta else {}
            rende = bool(conta.get('rende'))
            hoje = date.today()

            if abs(diff) < 0.01:
                self.dao.marcar_conciliacao(id_conta, hoje)
                self.dao.database_commit()
                return {'diferenca': 0.0, 'saldo_atual': saldo_atual,
                        'saldo_informado': saldo_informado, 'tipo': 'igual',
                        'id_lancamento': None}

            if diff > 0 and rende:
                tipo, natureza, nome_cat, desc = ('rendimento', 'receita',
                                                  'Rendimento',
                                                  'Rendimento · conciliação')
            elif diff > 0:
                tipo, natureza, nome_cat, desc = ('ajuste_positivo', 'receita',
                                                  'Ajuste de conciliação',
                                                  'Ajuste de conciliação'
                                                  ' (entrada não registrada)')
            else:
                tipo, natureza, nome_cat, desc = ('ajuste_negativo', 'despesa',
                                                  'Ajuste de conciliação',
                                                  'Ajuste de conciliação'
                                                  ' (saída não registrada)')

            id_categoria = self._garantir_categoria(id_usuario, nome_cat,
                                                    1 if natureza == 'receita' else 2)
            id_lanc = self.lancamento_facade.criar_lancamento({
                'id_conta': id_conta,
                'natureza': natureza,
                'valor': abs(diff),
                'data': hoje.isoformat(),
                'descricao': desc,
                'id_categoria': id_categoria,
                'origem': 'conciliacao',
            })
            self.dao.marcar_conciliacao(id_conta, hoje)
            self.dao.database_commit()
            return {'diferenca': diff, 'saldo_atual': saldo_atual,
                    'saldo_informado': saldo_informado, 'tipo': tipo,
                    'id_lancamento': id_lanc, 'descricao': desc}
        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def _garantir_categoria(self, id_usuario: int, nome: str, id_tipo: int) -> int:
        """Devolve o id da categoria `nome` do usuário; cria se não existir."""
        cat_dao = ControleiCategoriaDAO()
        todas = convert_unique_dic_to_arrayDict(
            cat_dao.get_category(
                id_usuario=id_usuario, id_tipo_categoria=id_tipo))
        for c in todas:
            if str(c.get('dsc_categoria', '')).strip().lower() == nome.lower():
                return int(c['id_categoria'])
        novo = cat_dao.insert_categoria({'id_usuario': id_usuario,
                                         'dsc_categoria': nome,
                                         'id_tipo_categoria': id_tipo})
        cat_dao.database_commit()
        # insert pode devolver id (RETURNING) ou não — relê se preciso
        if isinstance(novo, int):
            return novo
        todas = convert_unique_dic_to_arrayDict(
            cat_dao.get_category(
                id_usuario=id_usuario, id_tipo_categoria=id_tipo))
        return int(next(c['id_categoria'] for c in todas
                        if str(c.get('dsc_categoria', '')).strip().lower() == nome.lower()))
