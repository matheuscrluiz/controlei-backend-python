import re
import hashlib
from collections import Counter
from ...util.exceptions import FacadeException
from ...util.ofx_parser import parse_ofx
from ...util import controlei_csv_ingestor
from ..dao.controlei_compra_dao import ControleiCompraDAO
from ..dao.controlei_lancamento_dao import ControleiLancamentoDAO
from ..dao.controlei_import_layout_dao import ControleiImportLayoutDAO
from .controlei_compra_facade import ControleiCompraFacade
from .controlei_lancamento_facade import ControleiLancamentoFacade
from ...util import controlei_pdf_ingestor


def _chave_desc(desc) -> str:
    """Normaliza a descrição para casar histórico (maiúsculas, só letras)."""
    if not desc:
        return ''
    s = str(desc).upper()
    s = re.sub(r'[^A-ZÀ-Ú ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def _hash_item(destino, id_destino, data, valor, descricao) -> str:
    """Identificador de dedup para formatos sem ID nativo (CSV/PDF)."""
    base = f"{destino}|{id_destino}|{data}|{valor}|{_chave_desc(descricao)}"
    return 'h' + hashlib.sha1(base.encode('utf-8')).hexdigest()[:24]


class ControleiImportacaoFacade():

    def __init__(self):
        self.compra_dao = ControleiCompraDAO()
        self.compra_facade = ControleiCompraFacade()
        self.lancamento_dao = ControleiLancamentoDAO()
        self.lancamento_facade = ControleiLancamentoFacade()
        self.layout_dao = ControleiImportLayoutDAO()

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

    def normalizar_e_classificar(self, itens_canonicos, destino, id_destino):
        """Estágio 2 (comum a todos os formatos). A partir de itens
        canônicos {id_externo, data, descricao, valor(com sinal)}:
        classifica, deduplica e autocategoriza.
        destino: 'cartao' (gera compras) | 'conta' (gera lançamentos).
        A saída é idêntica à dos previews antigos (chave de dedup em
        'fitid', seja FITID do OFX ou hash de conteúdo)."""
        rotina = 'normalizar_e_classificar'

        try:
            if destino == 'cartao':
                sugestoes = self._mapa_sugestoes(id_destino)
                nome_norm = ''
            else:
                sugestoes = self._mapa_sugestoes_conta(id_destino)
                nome_norm = _chave_desc(
                    self.lancamento_dao.get_nome_dono_conta(id_destino))

            itens = []

            for c in itens_canonicos:
                valor = c.get('valor')
                data = c.get('data')
                descricao = c.get('descricao') or ''

                # chave de dedup: ID nativo (FITID) ou hash de conteúdo
                ref = c.get('id_externo') or _hash_item(
                    destino, id_destino, data, valor, descricao)

                if destino == 'cartao':
                    duplicada = bool(
                        ref and self.compra_dao.existe_import_ref(
                            id_destino, ref))
                else:
                    duplicada = bool(
                        ref and self.lancamento_dao.existe_import_ref(
                            id_destino, ref))

                memo = descricao.lower()
                memo_norm = _chave_desc(descricao)

                if destino == 'cartao':
                    eh_compra = valor < 0
                    sugerida = (
                        sugestoes.get(memo_norm) if eh_compra else None)
                    itens.append({
                        'fitid': ref,
                        'data': data,
                        'descricao': descricao,
                        'valor': abs(valor),
                        'tipo': 'compra' if eh_compra else 'credito',
                        'duplicada': duplicada,
                        'id_categoria': sugerida,
                        'confianca': c.get('confianca'),
                        'selecionar': eh_compra and not duplicada,
                    })
                else:
                    natureza = 'receita' if valor > 0 else 'despesa'
                    eh_pgto_fatura = (
                        'pagamento' in memo and 'fatura' in memo)
                    eh_investimento = any(
                        k in memo for k in
                        ('aplicac', 'resgate', 'rdb', 'cdb', 'tesouro'))
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
                    sugerida = (
                        sugestoes.get(memo_norm) if eh_normal else None)
                    itens.append({
                        'fitid': ref,
                        'data': data,
                        'descricao': descricao,
                        'valor': abs(valor),
                        'natureza': natureza,
                        'tipo': tipo,
                        'duplicada': duplicada,
                        'id_categoria': sugerida,
                        'confianca': c.get('confianca'),
                        'selecionar': (not duplicada) and eh_normal,
                    })

            return itens

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def preview_ofx(self, conteudo_bytes, id_cartao: int):
        """Importa fatura (OFX) -> itens de compra para revisão."""
        rotina = 'preview_ofx'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão é obrigatório')

            canon = [
                {'id_externo': t.get('fitid'), 'data': t['data'],
                 'descricao': t['descricao'], 'valor': t['valor']}
                for t in parse_ofx(conteudo_bytes)
            ]
            return self.normalizar_e_classificar(canon, 'cartao', id_cartao)

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
        """Importa extrato (OFX) -> lançamentos para revisão."""
        rotina = 'preview_ofx_conta'

        try:
            if not id_conta:
                raise FacadeException(
                    __file__, rotina, 'Conta é obrigatória')

            canon = [
                {'id_externo': t.get('fitid'), 'data': t['data'],
                 'descricao': t['descricao'], 'valor': t['valor']}
                for t in parse_ofx(conteudo_bytes)
            ]
            return self.normalizar_e_classificar(canon, 'conta', id_conta)

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

    # =====================================================================
    # CSV (fatura ou extrato) -> mesmo estágio 2 + memória de layout
    # =====================================================================
    def inspecionar_csv(self, conteudo_bytes, destino: str, id_destino: int):
        """Lê o CSV e: se já houver layout salvo para a assinatura do
        cabeçalho, devolve direto o preview; senão devolve o palpite de
        mapeamento para o usuário confirmar."""
        rotina = 'inspecionar_csv'

        try:
            if not id_destino:
                raise FacadeException(
                    __file__, rotina, 'Destino é obrigatório')

            colunas, linhas = controlei_csv_ingestor.ler_csv(conteudo_bytes)
            if not colunas:
                raise FacadeException(
                    __file__, rotina, 'CSV vazio ou ilegível')

            assin = controlei_csv_ingestor.assinatura(colunas)
            id_usuario = self.layout_dao.resolve_usuario(destino, id_destino)
            salvo = self.layout_dao.get_layout(id_usuario, assin)

            if salvo:
                canon = controlei_csv_ingestor.aplicar_mapeamento(
                    colunas, linhas, salvo, destino)
                itens = self.normalizar_e_classificar(
                    canon, destino, id_destino)
                return {'status': 'preview', 'assinatura': assin,
                        'itens': itens}

            palpite = controlei_csv_ingestor.adivinhar_mapeamento(
                colunas, linhas, destino)
            return {
                'status': 'mapeamento',
                'assinatura': assin,
                'colunas': colunas,
                'amostra': linhas[:5],
                'palpite': palpite,
            }

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def preview_csv(self, conteudo_bytes, destino: str, id_destino: int,
                    mapeamento: dict, salvar: bool = True):
        """Aplica o mapeamento, opcionalmente memoriza o layout, e devolve
        o preview pronto para revisão."""
        rotina = 'preview_csv'

        try:
            if not id_destino:
                raise FacadeException(
                    __file__, rotina, 'Destino é obrigatório')
            if not mapeamento or not mapeamento.get('data') \
                    or not mapeamento.get('valor'):
                raise FacadeException(
                    __file__, rotina,
                    'Mapeamento precisa de pelo menos data e valor')

            colunas, linhas = controlei_csv_ingestor.ler_csv(conteudo_bytes)
            canon = controlei_csv_ingestor.aplicar_mapeamento(
                colunas, linhas, mapeamento, destino)

            if salvar:
                id_usuario = self.layout_dao.resolve_usuario(
                    destino, id_destino)
                self.layout_dao.upsert_layout(
                    id_usuario, controlei_csv_ingestor.assinatura(
                        colunas), mapeamento)
                self.layout_dao.database_commit()

            itens = self.normalizar_e_classificar(canon, destino, id_destino)
            return {'status': 'preview', 'itens': itens}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    # =====================================================================
    # PDF (fatura ou extrato) -> heurística + mesmo estágio 2
    # =====================================================================
    def preview_pdf(self, conteudo_bytes, destino: str, id_destino: int):
        """Extrai transações do PDF (pdfplumber) e devolve o preview.
        pdfplumber é importado de forma lazy para não exigir a dependência
        quando o PDF não for usado."""
        rotina = 'preview_pdf'

        try:
            if not id_destino:
                raise FacadeException(
                    __file__, rotina, 'Destino é obrigatório')

            canon = controlei_pdf_ingestor.extrair_de_pdf(conteudo_bytes)

            # fatura: valores costumam vir positivos (gasto) -> compra (<0)
            if destino == 'cartao':
                for c in canon:
                    c['valor'] = -c['valor']

            itens = self.normalizar_e_classificar(canon, destino, id_destino)
            return {'status': 'preview', 'itens': itens}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
