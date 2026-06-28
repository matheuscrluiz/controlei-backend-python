import re
from collections import Counter
from ...util.exceptions import FacadeException
from ...util.ofx_parser import parse_ofx
from ..dao.controlei_compra_dao import ControleiCompraDAO
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO
from .controlei_compra_facade import ControleiCompraFacade
from .controlei_lancamento_facade import ControleiLancamentoFacade


def _chave_desc(desc) -> str:
    """Normaliza a descrição para casar histórico (maiúsculas, só letras)."""
    if not desc:
        return ''
    s = str(desc).upper()
    s = re.sub(r'[^A-ZÀ-Ú ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


class ControleiImportacaoFacade():

    def __init__(self):
        self.compra_dao = ControleiCompraDAO()
        self.compra_facade = ControleiCompraFacade()
        self.lancamento_dao = ControleiLancamentoDAO()
        self.lancamento_facade = ControleiLancamentoFacade()

    def _mapa_sugestoes(self, id_cartao: int) -> dict:
        """chave_desc -> id_categoria mais frequente no histórico do dono."""
        historico = self.compra_dao.get_categorias_historico(id_cartao)
        mapa = {}
        for h in historico:
            chave = _chave_desc(h.get('dsc_compra'))
            if not chave or h.get('id_categoria') is None:
                continue
            mapa.setdefault(chave, Counter())[int(h['id_categoria'])] += 1
        return {k: c.most_common(1)[0][0] for k, c in mapa.items()}

    def _mapa_sugestoes_conta(self, id_conta: int) -> dict:
        """chave_desc -> id_categoria mais frequente no histórico de
        lançamentos do dono da conta."""
        historico = self.lancamento_dao.get_categorias_historico(id_conta)
        mapa = {}
        for h in historico:
            chave = _chave_desc(h.get('descricao'))
            if not chave or h.get('id_categoria') is None:
                continue
            mapa.setdefault(chave, Counter())[int(h['id_categoria'])] += 1
        return {k: c.most_common(1)[0][0] for k, c in mapa.items()}

    def preview_ofx(self, conteudo_bytes, id_cartao: int):
        """Parseia o OFX e devolve a lista de itens para revisão.
        Não grava nada. Classifica compra (valor < 0) x crédito (>= 0)
        e marca duplicadas pelo FITID."""
        rotina = 'preview_ofx'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão é obrigatório')

            transacoes = parse_ofx(conteudo_bytes)
            sugestoes = self._mapa_sugestoes(id_cartao)
            itens = []

            for t in transacoes:
                eh_compra = t['valor'] < 0
                fitid = t.get('fitid')
                duplicada = bool(
                    fitid and self.compra_dao.existe_import_ref(
                        id_cartao, fitid))

                sugerida = (
                    sugestoes.get(_chave_desc(t['descricao']))
                    if eh_compra else None
                )

                itens.append({
                    'fitid': fitid,
                    'data': t['data'],
                    'descricao': t['descricao'],
                    'valor': abs(t['valor']),
                    'tipo': 'compra' if eh_compra else 'credito',
                    'duplicada': duplicada,
                    'id_categoria': sugerida,
                    # sugestão inicial: marcar só compras novas
                    'selecionar': eh_compra and not duplicada,
                })

            return itens

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def confirmar(self, id_cartao: int, itens: list):
        """Cria as compras dos itens selecionados, pulando duplicadas
        (dedup por FITID). Cada compra cai na fatura certa pelo ciclo
        do cartão (data_compra)."""
        rotina = 'confirmar'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão é obrigatório')

            criadas = 0
            puladas = 0

            for it in (itens or []):
                fitid = it.get('fitid')

                if fitid and self.compra_dao.existe_import_ref(
                        id_cartao, fitid):
                    puladas += 1
                    continue

                self.compra_facade.criar_compra({
                    'id_cartao': id_cartao,
                    'id_categoria': it.get('id_categoria'),
                    'dsc_compra': it.get('descricao'),
                    'valor_total': it.get('valor'),
                    'data_compra': it.get('data'),
                    'num_parcelas': 1,
                    'import_ref': fitid,
                })
                criadas += 1

            return {'criadas': criadas, 'puladas': puladas}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    # =====================================================================
    # EXTRATO DE CONTA (OFX -> lançamentos)
    # =====================================================================
    def preview_ofx_conta(self, conteudo_bytes, id_conta: int):
        """Parseia o OFX de extrato e devolve os itens para revisão.
        Não grava. natureza: valor > 0 = receita; valor < 0 = despesa.
        Marca duplicadas pelo FITID."""
        rotina = 'preview_ofx_conta'

        try:
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'Conta é obrigatória')

            transacoes = parse_ofx(conteudo_bytes)
            sugestoes = self._mapa_sugestoes_conta(id_conta)
            nome_norm = _chave_desc(
                self.lancamento_dao.get_nome_dono_conta(id_conta))
            itens = []

            for t in transacoes:
                natureza = 'receita' if t['valor'] > 0 else 'despesa'
                fitid = t.get('fitid')
                duplicada = bool(
                    fitid and self.lancamento_dao.existe_import_ref(
                        id_conta, fitid))

                memo = (t['descricao'] or '').lower()
                memo_norm = _chave_desc(t['descricao'])

                # Movimentos que NÃO são despesa/receita de verdade (entrariam
                # em duplicidade ou distorceriam relatórios) -> desmarcados.
                eh_pgto_fatura = ('pagamento' in memo and 'fatura' in memo)
                eh_investimento = any(
                    k in memo for k in
                    ('aplicac', 'resgate', 'rdb', 'cdb', 'tesouro'))
                # transferência entre as próprias contas: a contraparte do
                # Pix/TED é o próprio titular (nome bate no memo).
                eh_transf_propria = (
                    bool(nome_norm) and len(nome_norm) >= 6
                    and nome_norm in memo_norm
                    and ('transfer' in memo or 'pix' in memo
                         or 'ted' in memo))

                if eh_pgto_fatura:
                    tipo = 'pagamento_fatura'
                elif eh_investimento:
                    tipo = 'investimento'
                elif eh_transf_propria:
                    tipo = 'transferencia'
                else:
                    tipo = natureza

                eh_normal = tipo in ('receita', 'despesa')
                sugerida = sugestoes.get(memo_norm) if eh_normal else None

                itens.append({
                    'fitid': fitid,
                    'data': t['data'],
                    'descricao': t['descricao'],
                    'valor': abs(t['valor']),
                    'natureza': natureza,
                    'tipo': tipo,
                    'duplicada': duplicada,
                    'id_categoria': sugerida,
                    'selecionar': (not duplicada) and eh_normal,
                })

            return itens

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def confirmar_conta(self, id_conta: int, itens: list):
        """Cria os lançamentos dos itens selecionados (dedup por FITID).
        Já entram efetivados (movimento que de fato ocorreu na conta)."""
        rotina = 'confirmar_conta'

        try:
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'Conta é obrigatória')

            criadas = 0
            puladas = 0

            for it in (itens or []):
                fitid = it.get('fitid')

                if fitid and self.lancamento_dao.existe_import_ref(
                        id_conta, fitid):
                    puladas += 1
                    continue

                self.lancamento_facade.criar_lancamento({
                    'id_conta': id_conta,
                    'id_categoria': it.get('id_categoria'),
                    'natureza': it.get('natureza'),
                    'valor': it.get('valor'),
                    'data': it.get('data'),
                    'descricao': it.get('descricao'),
                    'status': 'efetivado',
                    'import_ref': fitid,
                })
                criadas += 1

            return {'criadas': criadas, 'puladas': puladas}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
