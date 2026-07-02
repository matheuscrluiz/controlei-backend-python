from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ..dao.controlei_compra_dao import ControleiCompraDAO
from ..dao.controlei_cartao_dao import ControleiCartaoDAO
from .controlei_fatura_facade import ControleiFaturaFacade
from .controlei_fatura_item_facade import ControleiFaturaItemFacade


def _normalizar_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), '%Y-%m-%d').date()


def _proximo_mes(ano: int, mes: int):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _add_meses(competencia: date, n: int) -> date:
    """Soma n meses a uma competência (1º dia do mês)."""
    total = (competencia.month - 1) + n
    ano = competencia.year + total // 12
    mes = total % 12 + 1
    return date(ano, mes, 1)


def _competencia_base(data_compra: date, dia_fechamento: int) -> date:
    """
    Mês da PRIMEIRA parcela. Compra antes do fechamento
    cai na fatura deste mês;
    a partir do fechamento (inclusive) rola pro mês seguinte.
    """
    if data_compra.day < dia_fechamento:
        ano, mes = data_compra.year, data_compra.month
    else:
        ano, mes = _proximo_mes(data_compra.year, data_compra.month)
    return date(ano, mes, 1)


def _dividir_parcelas(valor_total, num_parcelas):
    """Divide o total em N parcelas; a última absorve a sobra de centavos."""
    total = Decimal(str(valor_total))
    n = int(num_parcelas)
    base = (total / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    valores = [base] * (n - 1)
    valores.append(total - base * (n - 1))
    return valores


class ControleiCompraFacade():

    def __init__(self):
        """construtor da classe ControleiCompraFacade"""
        self.dao = ControleiCompraDAO()
        self.cartao_dao = ControleiCartaoDAO()
        self.fatura_facade = ControleiFaturaFacade()
        self.item_facade = ControleiFaturaItemFacade()

    def obter_compra(self, id_compra=None, id_cartao=None,
                     id_usuario=None, com_parcelas=False) -> dict:
        rotina = 'obter_compra'

        try:
            compras = self.dao.get_compra(
                id_compra=id_compra,
                id_cartao=id_cartao,
                id_usuario=id_usuario)
            compras = convert_unique_dic_to_arrayDict(compras)

            if com_parcelas and compras:
                for compra in compras:
                    compra['parcelas'] = self.dao.get_parcelas(
                        id_compra=compra['id_compra'])

            return compras

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_parcelas(self, id_compra=None, id_fatura=None):
        rotina = 'obter_parcelas'

        try:
            return self.dao.get_parcelas(
                id_compra=id_compra, id_fatura=id_fatura)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_compra(self, parm_dict: dict):
        """
        Cria a compra-pai e gera as N parcelas, cada uma alocada na fatura do
        mês correto. À vista no crédito = 1 parcela.
        """
        rotina = 'criar_compra'

        try:
            id_cartao = parm_dict.get('id_cartao')
            dsc_compra = (parm_dict.get('dsc_compra') or '').strip()
            valor_total = parm_dict.get('valor_total')
            num_parcelas = int(parm_dict.get('num_parcelas') or 1)

            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')
            if not dsc_compra:
                raise FacadeException(
                    __file__, rotina, 'Descrição da compra é obrigatória')
            if not valor_total or Decimal(str(valor_total)) <= 0:
                raise FacadeException(
                    __file__, rotina, 'Valor total deve ser maior que zero')
            if num_parcelas < 1:
                raise FacadeException(
                    __file__, rotina, 'Número de parcelas inválido')

            data_compra = _normalizar_data(
                parm_dict.get('data_compra') or date.today())

            # Cartão precisa ser de crédito (ter dia de fechamento).
            cartao = self.cartao_dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')
            dia_fechamento = cartao[0].get('dia_fechamento')
            if not dia_fechamento:
                raise FacadeException(
                    __file__, rotina,
                    'Compra no crédito exige cartão com dia de fechamento')

            # 1) Compra-pai (sem commit ainda; commit único no fim).
            id_compra = self.dao.insert_compra({
                'id_cartao': id_cartao,
                'id_categoria': parm_dict.get('id_categoria'),
                'dsc_compra': dsc_compra,
                'valor_total': valor_total,
                'data_compra': data_compra,
                'num_parcelas': num_parcelas,
                'pre_existente': parm_dict.get('pre_existente') or False,
                'id_recorrencia': parm_dict.get('id_recorrencia'),
                'import_ref': parm_dict.get('import_ref'),
            })

            # 2) Divide o valor e descobre o mês da 1ª parcela.
            valores = _dividir_parcelas(valor_total, num_parcelas)
            base = _competencia_base(data_compra, int(dia_fechamento))

            # 3) Cada parcela cai na fatura do seu mês (obter-ou-criar).
            for i in range(num_parcelas):
                competencia = _add_meses(base, i)
                fatura = self.fatura_facade.obter_ou_criar_fatura(
                    id_cartao, competencia)
                self.dao.insert_parcela({
                    'id_compra': id_compra,
                    'id_fatura': fatura['id_fatura'],
                    'numero': i + 1,
                    'valor_parcela': valores[i],
                })

            self.dao.database_commit()
            return id_compra

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def criar_credito_fatura(self, parm_dict: dict):
        """
        Cria um crédito/estorno (ex.: cashback) como item da fatura do mês
        correto. Abate o total da fatura (tipo 'credito' é normalizado como
        valor negativo pelo fatura_item_facade).
        """
        rotina = 'criar_credito_fatura'

        try:
            id_cartao = parm_dict.get('id_cartao')
            valor = parm_dict.get('valor')

            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')
            if not valor or Decimal(str(valor)) == 0:
                raise FacadeException(
                    __file__, rotina,
                    'Valor do crédito deve ser diferente de zero')

            data = _normalizar_data(
                parm_dict.get('data') or date.today())

            cartao = self.cartao_dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')
            dia_fechamento = cartao[0].get('dia_fechamento')
            if not dia_fechamento:
                raise FacadeException(
                    __file__, rotina,
                    'Crédito no cartão exige cartão com dia de fechamento')

            competencia = _competencia_base(data, int(dia_fechamento))
            fatura = self.fatura_facade.obter_ou_criar_fatura(
                id_cartao, competencia)

            return self.item_facade.criar_fatura_item({
                'id_fatura': fatura['id_fatura'],
                'tipo': 'credito',
                'valor': abs(Decimal(str(valor))),
                'descricao': (parm_dict.get('descricao') or '').strip()
                or 'Crédito importado',
            })

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_compra(self, parm_dict: dict):
        rotina = 'atualizar_compra'

        try:
            if not parm_dict.get('id_compra'):
                raise FacadeException(
                    __file__, rotina, 'ID da compra é obrigatório')

            compra = self.dao.get_compra(id_compra=parm_dict['id_compra'])
            if not compra:
                raise FacadeException(
                    __file__, rotina, 'Compra não encontrada')

            self.dao.update_compra(parm_dict)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def cancelar_compra(self, id_compra: int):
        """
        Cancela a compra: as parcelas NÃO pagas são removidas das faturas; as
        já pagas viram crédito (estorno) na fatura atual do cartão. A compra
        é marcada como cancelada.
        """
        rotina = 'cancelar_compra'

        try:
            if not id_compra:
                raise FacadeException(
                    __file__, rotina, 'ID da compra é obrigatório')

            compra = self.dao.get_compra(id_compra=id_compra)
            if not compra:
                raise FacadeException(
                    __file__, rotina, 'Compra não encontrada')
            compra = compra[0]

            if compra.get('cancelada'):
                raise FacadeException(
                    __file__, rotina, 'Compra já está cancelada')

            id_cartao = compra['id_cartao']
            parcelas = self.dao.get_parcelas(id_compra=id_compra)

            # A fatura que recebe os créditos é a fatura atual do cartão.
            # Criada sob demanda só se houver parcela paga.
            fatura_credito = None

            for parcela in parcelas:
                status = (parcela.get('status_fatura') or '').strip().lower()

                if status == 'paga':
                    if fatura_credito is None:
                        cartao = self.cartao_dao.get_cartao(
                            id_cartao=id_cartao)[0]
                        competencia = _competencia_base(
                            date.today(), int(cartao.get('dia_fechamento')))
                        fatura_credito = self.fatura_facade.\
                            obter_ou_criar_fatura(id_cartao, competencia)

                    self.item_facade.criar_fatura_item({
                        'id_fatura': fatura_credito['id_fatura'],
                        'tipo': 'estorno',
                        'valor': parcela['valor_parcela'],
                        'descricao': 'Estorno: %s' % compra.get('dsc_compra'),
                        'id_compra': id_compra,
                    })
                else:
                    # Parcela não paga: some da fatura.
                    self.dao.delete_parcela(parcela['id_parcela'])

            self.dao.marcar_cancelada(id_compra)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def deletar_compra(self, id_compra: int):
        """Exclusão dura (remove parcelas via cascade). O cancelamento com
        estorno das parcelas pagas virá no fluxo de fatura_item/estorno."""
        rotina = 'deletar_compra'

        try:
            if not id_compra:
                raise FacadeException(
                    __file__, rotina, 'ID da compra é obrigatório')

            compra = self.dao.get_compra(id_compra=id_compra)
            if not compra:
                raise FacadeException(
                    __file__, rotina, 'Compra não encontrada')

            self.dao.delete_compra(id_compra)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
