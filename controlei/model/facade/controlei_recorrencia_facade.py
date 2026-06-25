import calendar
from datetime import date, datetime
from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_recorrencia_dao import ControleiRecorrenciaDAO
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO
from ..dao.controlei_compra_dao import ControleiCompraDAO
from .controlei_compra_facade import ControleiCompraFacade

NATUREZAS_VALIDAS = ('receita', 'despesa')


def _normalizar_data(valor):
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), '%Y-%m-%d').date()


def _data_do_mes_atual(dia_do_mes: int) -> date:
    """Monta a data da ocorrência no mês corrente, limitando o dia ao mês."""
    hoje = date.today()
    ultimo = calendar.monthrange(hoje.year, hoje.month)[1]
    return date(hoje.year, hoje.month, min(int(dia_do_mes), ultimo))


class ControleiRecorrenciaFacade():

    def __init__(self):
        self.dao = ControleiRecorrenciaDAO()
        self.lancamento_dao = ControleiLancamentoDAO()
        self.compra_dao = ControleiCompraDAO()
        self.compra_facade = ControleiCompraFacade()

    def obter_recorrencia(self, **filtros) -> dict:
        rotina = 'obter_recorrencia'

        try:
            recs = self.dao.get_recorrencia(**filtros)
            return convert_unique_dic_to_arrayDict(recs)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def _validar(self, parm_dict, exigir_meio=True):
        id_conta = parm_dict.get('id_conta')
        id_cartao = parm_dict.get('id_cartao')
        natureza = (parm_dict.get('natureza') or '').strip().lower()
        variavel = bool(parm_dict.get('variavel'))

        if exigir_meio:
            # Exatamente um meio: conta OU cartão (o banco também garante).
            if bool(id_conta) == bool(id_cartao):
                raise FacadeException(
                    __file__, '_validar',
                    'Informe exatamente um meio: conta OU cartão')
        if natureza not in NATUREZAS_VALIDAS:
            raise FacadeException(
                __file__, '_validar', 'Natureza inválida (receita ou despesa)')
        if not (parm_dict.get('dsc_recorrencia') or '').strip():
            raise FacadeException(
                __file__, '_validar', 'Descrição é obrigatória')
        dia = parm_dict.get('dia_do_mes')
        if not dia or int(dia) < 1 or int(dia) > 31:
            raise FacadeException(
                __file__, '_validar', 'Dia do mês deve estar entre 1 e 31')
        if not variavel and (parm_dict.get('valor') is None):
            raise FacadeException(
                __file__, '_validar',
                'Valor é obrigatório (ou marque como variável)')
        # No crédito o valor precisa ser fixo (compra exige valor na geração).
        if id_cartao and variavel:
            raise FacadeException(
                __file__, '_validar',
                'Recorrência no crédito precisa ter valor fixo')

    def criar_recorrencia(self, parm_dict: dict):
        rotina = 'criar_recorrencia'

        try:
            if not parm_dict.get('id_usuario'):
                raise FacadeException(
                    __file__, rotina, 'ID do usuário é obrigatório')

            self._validar(parm_dict)

            id_recorrencia = self.dao.insert_recorrencia(parm_dict)
            self.dao.database_commit()

            return id_recorrencia

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_recorrencia(self, parm_dict: dict):
        rotina = 'atualizar_recorrencia'

        try:
            if not parm_dict.get('id_recorrencia'):
                raise FacadeException(
                    __file__, rotina, 'ID da recorrência é obrigatório')

            atual = self.dao.get_recorrencia(
                id_recorrencia=parm_dict['id_recorrencia'])
            if not atual:
                raise FacadeException(
                    __file__, rotina, 'Recorrência não encontrada')

            # O meio não muda na edição; valida o resto reusando o do registro.
            base = dict(atual[0])
            base.update(parm_dict)
            self._validar(base, exigir_meio=False)

            self.dao.update_recorrencia(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_recorrencia(self, id_recorrencia: int):
        rotina = 'deletar_recorrencia'

        try:
            if not id_recorrencia:
                raise FacadeException(
                    __file__, rotina, 'ID da recorrência é obrigatório')

            self.dao.delete_recorrencia(id_recorrencia)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def gerar_ocorrencia(self, id_recorrencia: int, data=None):
        """
        Materializa uma ocorrência do mês:
          - débito/conta -> lançamento 'previsto'
          (ou 'efetivado' se automático);
            recorrência variável entra com valor 0, pra você preencher ao
            confirmar.
          - crédito/cartão -> compra de 1x (cai na fatura do mês).
        O GATILHO (quando chamar isto) fica a cargo do
        job/preguiçoso; aqui só a materialização.
        """
        rotina = 'gerar_ocorrencia'

        try:
            rec = self.dao.get_recorrencia(id_recorrencia=id_recorrencia)
            if not rec:
                raise FacadeException(
                    __file__, rotina, 'Recorrência não encontrada')
            rec = rec[0]

            if not rec.get('ativa'):
                raise FacadeException(
                    __file__, rotina, 'Recorrência inativa')

            data_ocorrencia = _normalizar_data(data) if data \
                else _data_do_mes_atual(rec['dia_do_mes'])
            natureza = rec['natureza']
            descricao = rec['dsc_recorrencia']

            # --------- CRÉDITO: compra de 1x ---------
            if rec.get('id_cartao'):
                if rec.get('valor') is None:
                    raise FacadeException(
                        __file__, rotina,
                        'Recorrência de crédito sem valor não pode ser gerada')
                # idempotência: já existe compra dessa recorrência no mês?
                if self.compra_dao.existe_recorrencia_no_mes(
                        id_recorrencia, data_ocorrencia):
                    return {'gerado': False, 'motivo': 'ja_existe'}
                return self.compra_facade.criar_compra({
                    'id_cartao': rec['id_cartao'],
                    'id_categoria': rec.get('id_categoria'),
                    'dsc_compra': descricao,
                    'valor_total': rec['valor'],
                    'data_compra': data_ocorrencia,
                    'num_parcelas': 1,
                    'id_recorrencia': id_recorrencia,
                })

            # --------- DÉBITO/CONTA: lançamento previsto ---------
            # idempotência: já existe lançamento dessa recorrência no mês?
            existentes = self.lancamento_dao.get_lancamento(
                id_recorrencia=id_recorrencia)
            for e in existentes:
                d = _normalizar_data(e['data'])
                if (d.year == data_ocorrencia.year
                        and d.month == data_ocorrencia.month):
                    return {'gerado': False, 'motivo': 'ja_existe'}

            valor_base = rec.get('valor')
            if rec.get('variavel') or valor_base is None:
                valor_assinado = 0
                status = 'previsto'
            else:
                v = abs(Decimal(str(valor_base)))
                valor_assinado = v if natureza == 'receita' else -v
                status = 'efetivado' if rec.get('confirmar_automatico') \
                    else 'previsto'

            id_lancamento = self.lancamento_dao.insert_lancamento({
                'id_conta': rec['id_conta'],
                'id_categoria': rec.get('id_categoria'),
                'natureza': natureza,
                'valor': valor_assinado,
                'data': data_ocorrencia,
                'descricao': descricao,
                'id_recorrencia': id_recorrencia,
                'status': status,
            })
            self.lancamento_dao.database_commit()

            return id_lancamento

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
