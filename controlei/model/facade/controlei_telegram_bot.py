"""
Executor do bot do Telegram: recebe a interpretação de uma mensagem e FAZ.

Responsabilidades:
  1) mapear chat_id -> usuário;
  2) resolver o DESTINO (conta / benefício) com aprendizado:
       - só tem um? usa;
       - a pessoa disse o nome? casa por aproximação;
       - já registrou essa descrição antes? repete o destino da última vez;
       - senão pergunta UMA vez com botões e aprende (o próprio registro
         seguinte vira o "histórico");
  3) executar via os facades que já existem (zero lógica financeira nova);
  4) responder curto, com o que aconteceu + [Desfazer] (+ orçamento quando
     há), e tratar os cliques (callback_query).

Sem IA. Tudo determinístico e auditável.
"""
import json
import re
import unicodedata
from datetime import date, datetime

import pandas as pd

from ...util.controlei_telegram import (
    enviar_telegram, responder_callback, editar_mensagem)
from ...util.controlei_telegram_parser import interpretar, TEXTO_AJUDA
from ...util.exceptions import DAOException
from ..base import controlei_dao_base as base
from ..dao.controlei_conta_dao import ControleiContaDAO
from ..dao.controlei_derivados_dao import ControleiDerivadosDAO
from .controlei_lancamento_facade import ControleiLancamentoFacade
from .controlei_beneficio_facade import ControleiBeneficioFacade


# ---------------------------------------------------------------- helpers
def _sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s or '')
                   if unicodedata.category(c) != 'Mn').lower()


def _brl(v) -> str:
    v = float(v or 0)
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _casa(nome_dito: str, candidatos: list, chave: str):
    """Match aproximado por nome: contém / é contido / mesmo início.
    Devolve o candidato ou None se ambíguo/sem match."""
    if not nome_dito:
        return None
    dito = _sem_acento(nome_dito).strip()
    hits = []
    for c in candidatos:
        nome = _sem_acento(str(c.get(chave) or ''))
        if not nome:
            continue
        if dito == nome or dito in nome or nome in dito or nome.startswith(dito):
            hits.append(c)
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------- DAO de contexto
class _ContextoDAO(base.DAOBase):
    def __init__(self):
        super().__init__()

    def usuario_por_chat(self, chat_id: str):
        try:
            df = pd.read_sql(
                sql="""SELECT id_usuario, nome FROM usuario
                       WHERE telegram_chat_id = %(c)s AND notif_telegram_ativo""",
                con=self.get_connection(), params={'c': str(chat_id)})
            r = self.convert_dataframe_to_dict(df)
            return r[0] if r else None
        except DAOException as erro:
            raise DAOException(__file__, 'usuario_por_chat', erro)

    def get(self, chat_id: str):
        try:
            df = pd.read_sql(
                sql="SELECT * FROM telegram_contexto WHERE chat_id = %(c)s",
                con=self.get_connection(), params={'c': str(chat_id)})
            r = self.convert_dataframe_to_dict(df)
            return r[0] if r else None
        except DAOException as erro:
            raise DAOException(__file__, 'get', erro)

    def set_ultimo(self, chat_id, id_usuario, tipo, id_, resumo):
        try:
            self.execute_dml_command_parms("""
                INSERT INTO telegram_contexto
                    (chat_id, id_usuario, ultimo_tipo, ultimo_id, ultimo_resumo,
                     pendente, atualizado_em)
                VALUES (%(c)s, %(u)s, %(t)s, %(i)s, %(r)s, NULL, now())
                ON CONFLICT (chat_id) DO UPDATE SET
                    ultimo_tipo = EXCLUDED.ultimo_tipo,
                    ultimo_id = EXCLUDED.ultimo_id,
                    ultimo_resumo = EXCLUDED.ultimo_resumo,
                    pendente = NULL, atualizado_em = now()
            """, {'c': str(chat_id), 'u': id_usuario, 't': tipo, 'i': id_, 'r': resumo})
            self.database_commit()
        except DAOException as erro:
            raise DAOException(__file__, 'set_ultimo', erro)

    def set_pendente(self, chat_id, id_usuario, pendente: dict):
        try:
            self.execute_dml_command_parms("""
                INSERT INTO telegram_contexto (chat_id, id_usuario, pendente, atualizado_em)
                VALUES (%(c)s, %(u)s, %(p)s::jsonb, now())
                ON CONFLICT (chat_id) DO UPDATE SET
                    pendente = EXCLUDED.pendente, atualizado_em = now()
            """, {'c': str(chat_id), 'u': id_usuario, 'p': json.dumps(pendente, default=str)})
            self.database_commit()
        except DAOException as erro:
            raise DAOException(__file__, 'set_pendente', erro)

    def limpar_ultimo(self, chat_id):
        try:
            self.execute_dml_command_parms("""
                UPDATE telegram_contexto SET ultimo_tipo = NULL, ultimo_id = NULL,
                       ultimo_resumo = NULL WHERE chat_id = %(c)s
            """, {'c': str(chat_id)})
            self.database_commit()
        except DAOException as erro:
            raise DAOException(__file__, 'limpar_ultimo', erro)

    # aprendizado: onde essa descrição caiu da última vez?
    def destino_anterior(self, id_usuario: int, descricao: str):
        try:
            # Sem depender da extensão unaccent: busca as descrições recentes
            # do usuário e compara normalizado (sem acento) no Python.
            df = pd.read_sql(sql="""
                SELECT l.id_conta, l.descricao
                FROM lancamento l
                JOIN conta co ON co.id_conta = l.id_conta
                WHERE co.id_usuario = %(u)s
                  AND l.natureza IN ('receita','despesa')
                  AND l.descricao IS NOT NULL
                ORDER BY l.data DESC, l.id_lancamento DESC
                LIMIT 300
            """, con=self.get_connection(), params={'u': id_usuario})
            alvo = _sem_acento(descricao).strip()
            for r in self.convert_dataframe_to_dict(df):
                if _sem_acento(r.get('descricao') or '').strip() == alvo:
                    return int(r['id_conta'])
            return None
        except Exception:
            # sem extensão unaccent ou outro erro: sem aprendizado, sem quebrar
            return None

    def gasto_categoria_mes(self, id_usuario: int, id_categoria):
        """Pro rodapé de orçamento na resposta (opcional)."""
        if not id_categoria:
            return None
        try:
            df = pd.read_sql(sql="""
                SELECT o.valor_teto,
                       COALESCE((SELECT SUM(ABS(l.valor)) FROM lancamento l
                                 JOIN conta co ON co.id_conta = l.id_conta
                                 WHERE co.id_usuario = %(u)s AND l.natureza='despesa'
                                   AND l.status='efetivado' AND l.id_categoria = %(cat)s
                                   AND date_trunc('month', l.data) = date_trunc('month', CURRENT_DATE)),0)
                     + COALESCE((SELECT SUM(cp.valor_total) FROM compra cp
                                 JOIN cartao ca ON ca.id_cartao = cp.id_cartao
                                 JOIN conta co2 ON co2.id_conta = ca.id_conta
                                 WHERE co2.id_usuario = %(u)s AND cp.cancelada = false
                                   AND cp.id_categoria = %(cat)s
                                   AND date_trunc('month', cp.data_compra) = date_trunc('month', CURRENT_DATE)),0)
                       AS gasto
                FROM orcamento o
                WHERE o.id_usuario = %(u)s AND o.id_categoria = %(cat)s
                  AND (o.competencia IS NULL
                       OR o.competencia = date_trunc('month', CURRENT_DATE)::date)
                ORDER BY o.competencia DESC NULLS LAST LIMIT 1
            """, con=self.get_connection(), params={'u': id_usuario, 'cat': id_categoria})
            r = self.convert_dataframe_to_dict(df)
            return r[0] if r else None
        except Exception:
            return None


# ---------------------------------------------------------------- executor
class ControleiTelegramBot:

    def __init__(self):
        self.ctx = _ContextoDAO()
        self.conta_dao = ControleiContaDAO()
        self.deriv = ControleiDerivadosDAO()
        self.lanc = ControleiLancamentoFacade()
        self.ben = ControleiBeneficioFacade()

    # ---------- entrada: mensagem de texto ----------
    def tratar_mensagem(self, chat_id: str, texto: str):
        usr = self.ctx.usuario_por_chat(chat_id)
        if not usr:
            enviar_telegram(chat_id,
                            "Não achei seu Controlei vinculado a este chat. "
                            "Vincule em <b>Meu perfil → Telegram</b> no app.")
            return

        id_usuario = int(usr['id_usuario'])
        it = interpretar(texto)

        if it['intencao'] == 'ajuda':
            return enviar_telegram(chat_id, TEXTO_AJUDA)
        if it['intencao'] == 'consulta_saldo':
            return self._responder_saldo(chat_id, id_usuario)
        if it['intencao'] == 'consulta_gastos':
            return self._responder_gastos(chat_id, id_usuario)
        if it['intencao'] == 'desconhecido':
            return enviar_telegram(chat_id,
                                   f"🤔 {it['erro'] or 'Não entendi.'}\n\n{TEXTO_AJUDA}")

        # "187,40" sozinho (sem descrição) e há recorrência variável aguardando
        # valor → é a resposta ao pedido "quanto veio?": confirma a pendência
        if (it['intencao'] == 'gasto' and not it.get('descricao')
                and not it.get('destino')):
            pend = self._pendentes_variaveis(id_usuario)
            if pend:
                return self._confirmar_pendente(chat_id, id_usuario, pend, float(it['valor']))

        if it['intencao'] in ('gasto', 'receita'):
            return self._registrar_conta(chat_id, id_usuario, it)
        if it['intencao'] in ('beneficio_gasto', 'beneficio_recarga'):
            return self._registrar_beneficio(chat_id, id_usuario, it)

    # ---------- entrada: clique em botão ----------
    def tratar_callback(self, chat_id: str, message_id: int, callback_id: str, data: str):
        usr = self.ctx.usuario_por_chat(chat_id)
        if not usr:
            return responder_callback(callback_id, "Chat não vinculado.")
        id_usuario = int(usr['id_usuario'])

        # undo
        if data == 'undo':
            return self._desfazer(chat_id, message_id, callback_id)

        # mudar conta: desfaz o último registro e reabre a escolha
        if data == 'mudar':
            ctx = self.ctx.get(chat_id) or {}
            if ctx.get('ultimo_tipo') != 'lancamento' or not ctx.get('ultimo_id'):
                return responder_callback(callback_id, "Nada pra mudar.")
            try:
                # recupera o lançamento pra reconstruir a pendência
                r = self.lanc.obter_lancamento(
                    id_lancamento=int(ctx['ultimo_id']))
                lanc = r[0] if r else None
            except Exception:
                lanc = None
            if not lanc:
                return responder_callback(callback_id, "Não achei o registro.")
            self.lanc.deletar_lancamento(int(ctx['ultimo_id']))
            self.ctx.limpar_ultimo(chat_id)
            pend = {
                'intencao': 'gasto' if lanc.get('natureza') == 'despesa' else 'receita',
                'valor': abs(float(lanc.get('valor') or 0)),
                'descricao': lanc.get('descricao') or '',
                'destino': None, 'data': str(lanc.get('data'))[:10],
            }
            self.ctx.set_pendente(chat_id, id_usuario, pend)
            contas = self._lista(
                self.conta_dao.get_conta(id_usuario=id_usuario))
            botoes = [
                [(c['apelido'], f"dest:conta:{int(c['id_conta'])}")] for c in contas[:6]]
            responder_callback(callback_id)
            editar_mensagem(chat_id, message_id,
                            f"↔ {_brl(pend['valor'])} · {pend['descricao']} — em qual conta?")
            return enviar_telegram(chat_id, "Escolha a conta <i>(vou lembrar pra próxima)</i>:", botoes)

        # confirmação de recorrência variável: conf:<id_lancamento>
        m = re.match(r'^conf:(\d+)$', data)
        if m:
            ctx = self.ctx.get(chat_id) or {}
            pend = ctx.get('pendente')
            if isinstance(pend, str):
                try:
                    pend = json.loads(pend)
                except ValueError:
                    pend = None
            valor = (pend or {}).get('confirmar_valor')
            if valor is None:
                return responder_callback(callback_id, "Esse pedido já foi resolvido.")
            self.lanc.confirmar_lancamento(int(m.group(1)), float(valor))
            self.ctx.set_pendente(chat_id, id_usuario, {})
            responder_callback(callback_id, "Confirmado.")
            return editar_mensagem(chat_id, message_id, f"✅ Confirmado: {_brl(valor)}")

        # escolha de destino: dest:conta:<id> | dest:ben:<id>
        m = re.match(r'^dest:(conta|ben):(\d+)$', data)
        if m:
            ctx = self.ctx.get(chat_id) or {}
            pend = ctx.get('pendente')
            if isinstance(pend, str):
                try:
                    pend = json.loads(pend)
                except ValueError:
                    pend = None
            if not pend:
                responder_callback(
                    callback_id, "Esse registro já foi resolvido.")
                return
            responder_callback(callback_id)
            pend['data'] = pend.get('data')
            if m.group(1) == 'conta':
                pend['_id_conta'] = int(m.group(2))
                self._registrar_conta(
                    chat_id, id_usuario, pend, message_id=message_id)
            else:
                pend['_id_beneficio'] = int(m.group(2))
                self._registrar_beneficio(
                    chat_id, id_usuario, pend, message_id=message_id)
            return

        responder_callback(callback_id)

    # ---------- recorrência variável aguardando valor ----------
    def _pendentes_variaveis(self, id_usuario):
        """Lançamentos 'previsto' com valor 0 (recorrência variável)."""
        try:
            todos = self.lanc.obter_lancamento(
                id_usuario=id_usuario, status='previsto')
            hoje = date.today()
            # só as que já chegaram no dia: o job gera o mês inteiro no dia
            # 1, mas "quanto veio?" só faz sentido depois da data
            return [l for l in (todos or [])
                    if abs(float(l.get('valor') or 0)) < 0.005
                    and datetime.strptime(str(l.get('data'))[:10], '%Y-%m-%d').date() <= hoje]
        except Exception:
            return []

    def _confirmar_pendente(self, chat_id, id_usuario, pend, valor: float):
        if len(pend) == 1:
            l = pend[0]
            self.lanc.confirmar_lancamento(int(l['id_lancamento']), valor)
            return enviar_telegram(chat_id,
                                   f"✅ <b>{l.get('descricao') or 'Conta fixa'}</b> confirmada: "
                                   f"{_brl(valor)}\n{l.get('apelido') or ''} · {str(l.get('data'))[:10]}")
        # várias aguardando: pergunta qual, guardando o valor
        self.ctx.set_pendente(chat_id, id_usuario, {'confirmar_valor': valor})
        botoes = [[(f"{l.get('descricao')} ({str(l.get('data'))[:10]})",
                    f"conf:{int(l['id_lancamento'])}")] for l in pend[:6]]
        return enviar_telegram(chat_id,
                               f"{_brl(valor)} é de qual conta fixa?", botoes)

    # ---------- registrar em CONTA (gasto / receita) ----------
    def _registrar_conta(self, chat_id, id_usuario, it: dict, message_id=None):
        contas = self._lista(self.conta_dao.get_conta(id_usuario=id_usuario))
        if not contas:
            return enviar_telegram(chat_id, "Você ainda não tem contas cadastradas no Controlei.")

        id_conta = it.get('_id_conta')
        descricao = it.get('descricao') or ''
        veio_do_historico = False

        if not id_conta:
            # 1) a pessoa disse o nome?
            if it.get('destino'):
                c = _casa(it['destino'], contas, 'apelido')
                if c:
                    id_conta = int(c['id_conta'])
                else:
                    # não é conta: era parte da descrição ("no mercado")
                    descricao = (descricao + ' ' + it['destino']).strip()
                    it['descricao'] = descricao
            # 2) só uma conta
            if not id_conta and len(contas) == 1:
                id_conta = int(contas[0]['id_conta'])
            # 3) aprendizado: repete a conta da ÚLTIMA vez com essa descrição.
            #    Como é sempre a mais recente, mudar de conta é só dizer o nome
            #    uma vez ("salário no nubank") — daí em diante vai pro Nubank.
            if not id_conta and descricao:
                id_conta = self.ctx.destino_anterior(id_usuario, descricao)
                veio_do_historico = id_conta is not None
            # 4) pergunta com botões (uma vez; aprende no próximo)
            if not id_conta:
                try:
                    self.ctx.set_pendente(
                        chat_id, id_usuario,
                        {k: v for k, v in it.items() if not k.startswith('_')})
                    botoes = [[(c['apelido'], f"dest:conta:{int(c['id_conta'])}")]
                              for c in contas[:6]]
                    return enviar_telegram(chat_id,
                                           f"{_brl(it['valor'])} · <b>{descricao or 'Despesa'}</b>\n"
                                           f"Em qual conta? <i>(vou lembrar pra próxima)</i>", botoes)
                except Exception:
                    # sem a tabela de contexto não dá pra "perguntar e lembrar":
                    # usa a 1ª conta (melhor que travar; o usuário vê onde caiu)
                    id_conta = int(contas[0]['id_conta'])

        natureza = 'despesa' if it['intencao'] == 'gasto' else 'receita'
        dt = it.get('data')
        dt = dt if isinstance(dt, date) else datetime.strptime(
            str(dt)[:10], '%Y-%m-%d').date()
        id_lanc = self.lanc.criar_lancamento({
            'id_conta': id_conta,
            'natureza': natureza,
            'valor': float(it['valor']),
            'data': dt.isoformat(),
            'descricao': descricao or ('Despesa' if natureza == 'despesa' else 'Receita'),
            'id_categoria': None,
        })
        conta_nome = next((c['apelido']
                          for c in contas if int(c['id_conta']) == id_conta), '')
        resumo = f"{_brl(it['valor'])} · {descricao or natureza.title()}"
        tem_undo = self._guardar_ultimo(
            chat_id, id_usuario, 'lancamento', id_lanc, resumo)

        sinal = '💸' if natureza == 'despesa' else '💰'
        quando = 'hoje' if dt == date.today() else dt.strftime('%d/%m')
        origem = " · <i>como da última vez</i>" if veio_do_historico else ""
        texto = (f"{sinal} <b>{'Gasto' if natureza == 'despesa' else 'Receita'} {_brl(it['valor'])}</b> · "
                 f"{descricao or natureza.title()}\n{quando} · {conta_nome}{origem}")
        botoes = [[("↩ Desfazer", "undo")]]
        if len(contas) > 1:
            # troca de conta em 1 toque: desfaz este e reabre a escolha com
            # os mesmos dados — a nova escolha vira o "último" e reensina
            botoes[0].append(("↔ Mudar conta", "mudar")) if tem_undo else None
        if message_id:
            editar_mensagem(chat_id, message_id, texto)
            return enviar_telegram(chat_id, "✅ Registrado.", botoes)
        return enviar_telegram(chat_id, texto, botoes)

    # ---------- registrar em BENEFÍCIO (gasto / recarga) ----------
    def _registrar_beneficio(self, chat_id, id_usuario, it: dict, message_id=None):
        bens = self.ben.listar(id_usuario)
        if not bens:
            return enviar_telegram(chat_id,
                                   "Você ainda não tem benefícios. Cadastre em <b>Benefícios</b> no app.")

        id_ben = it.get('_id_beneficio')
        if not id_ben:
            if it.get('destino'):
                # casa pelo nome OU pelo tipo (va/vr/vt)
                b = _casa(it['destino'], bens, 'dsc_beneficio') or \
                    next((x for x in bens if _sem_acento(x.get('tipo', ''))
                         == _sem_acento(it['destino'])), None)
                if b:
                    id_ben = int(b['id_beneficio'])
            if not id_ben and len(bens) == 1:
                id_ben = int(bens[0]['id_beneficio'])
            if not id_ben:
                try:
                    self.ctx.set_pendente(
                        chat_id, id_usuario,
                        {k: v for k, v in it.items() if not k.startswith('_')})
                    botoes = [[(b['dsc_beneficio'], f"dest:ben:{int(b['id_beneficio'])}")]
                              for b in bens[:6]]
                    acao = 'Recarga' if it['intencao'] == 'beneficio_recarga' else 'Gasto'
                    return enviar_telegram(chat_id,
                                           f"{acao} de {_brl(it['valor'])}. Em qual benefício?", botoes)
                except Exception:
                    id_ben = int(bens[0]['id_beneficio'])

        tipo = 'recarga' if it['intencao'] == 'beneficio_recarga' else 'gasto'
        dt = it.get('data')
        dt = dt if isinstance(dt, date) else datetime.strptime(
            str(dt)[:10], '%Y-%m-%d').date()
        self.ben.movimentar({
            'id_beneficio': id_ben, 'tipo': tipo, 'valor': float(it['valor']),
            'data': dt.isoformat(), 'descricao': it.get('descricao') or None,
        })
        # id do movimento pra Desfazer: pega o mais recente do benefício
        ext = self.ben.extrato(id_ben, dt.isoformat())
        movs = ext.get('movimentos') or []
        id_mov = int(movs[0]['id_beneficio_mov']) if movs else None
        ben_nome = next((b['dsc_beneficio']
                        for b in bens if int(b['id_beneficio']) == id_ben), '')
        saldo = float(
            next((b['saldo'] for b in bens if int(b['id_beneficio']) == id_ben), 0) or 0)
        saldo_novo = saldo + \
            (float(it['valor']) if tipo == 'recarga' else -float(it['valor']))

        resumo = f"{_brl(it['valor'])} · {(it.get('descricao') or tipo.title())} ({ben_nome})"
        tem_undo = bool(id_mov) and self._guardar_ultimo(
            chat_id, id_usuario, 'beneficio_mov', id_mov, resumo)

        emoji = '🔋' if tipo == 'recarga' else '🏦'
        texto = (f"{emoji} <b>{tipo.title()} {_brl(it['valor'])}</b>"
                 f"{(' · ' + it['descricao']) if it.get('descricao') else ''}\n"
                 f"{ben_nome} · saldo agora <b>{_brl(saldo_novo)}</b>")
        botoes = [[("↩ Desfazer", "undo")]] if tem_undo else None
        if message_id:
            editar_mensagem(chat_id, message_id, texto)
            return enviar_telegram(chat_id, "✅ Registrado.", botoes)
        return enviar_telegram(chat_id, texto, botoes)

    def _guardar_ultimo(self, chat_id, id_usuario, tipo, id_, resumo) -> bool:
        """Guarda o último registro pro Desfazer. Se a tabela de contexto não
        existir (migração não rodou) NÃO derruba o registro — só desabilita
        o botão Desfazer nesta resposta."""
        try:
            self.ctx.set_ultimo(chat_id, id_usuario, tipo, id_, resumo)
            return True
        except Exception:
            return False

    # ---------- desfazer ----------
    def _desfazer(self, chat_id, message_id, callback_id):
        ctx = self.ctx.get(chat_id) or {}
        tipo, id_ = ctx.get('ultimo_tipo'), ctx.get('ultimo_id')
        if not tipo or not id_:
            return responder_callback(callback_id, "Nada pra desfazer.")
        try:
            if tipo == 'lancamento':
                self.lanc.deletar_lancamento(int(id_))
            elif tipo == 'beneficio_mov':
                self.ben.deletar_movimento(int(id_))
            self.ctx.limpar_ultimo(chat_id)
            responder_callback(callback_id, "Desfeito.")
            editar_mensagem(chat_id, message_id,
                            f"↩ <s>{ctx.get('ultimo_resumo') or 'registro'}</s> — desfeito.")
        except Exception:
            responder_callback(callback_id, "Não consegui desfazer.")

    # ---------- consultas ----------
    def _responder_saldo(self, chat_id, id_usuario):
        saldos = self._lista(self.deriv.get_saldos_por_conta(id_usuario))
        patr = self._lista(self.deriv.get_patrimonio_usuario(id_usuario))
        patr = patr[0] if patr else {}
        linhas = [
            f"• {s['apelido']}: <b>{_brl(s['saldo'])}</b>" for s in saldos]
        bens = self.ben.listar(id_usuario)
        if bens:
            linhas.append("")
            linhas += [
                f"🏦 {b['dsc_beneficio']}: <b>{_brl(b['saldo'])}</b>" for b in bens]
        texto = ("💼 <b>Patrimônio: " + _brl(patr.get('patrimonio')) + "</b>\n"
                 + "\n".join(linhas))
        if patr.get('divida'):
            texto += f"\n\n💳 devendo {_brl(patr['divida'])} no cartão"
        return enviar_telegram(chat_id, texto)

    def _responder_gastos(self, chat_id, id_usuario):
        hoje = date.today()
        ini = hoje.replace(day=1).isoformat()
        cats = self._lista(self.deriv.get_despesas_por_categoria(
            id_usuario, ini, hoje.isoformat()))
        total = sum(float(c.get('total') or 0) for c in cats)
        top = sorted(cats, key=lambda c: -float(c.get('total') or 0))[:5]
        linhas = [
            f"• {c.get('dsc_categoria') or 'Sem categoria'}: <b>{_brl(c['total'])}</b>" for c in top]
        texto = (f"📊 <b>Gastos em {hoje.strftime('%B').lower()}: {_brl(total)}</b>\n"
                 + ("\n".join(linhas) if linhas else "Nenhum gasto registrado ainda."))
        return enviar_telegram(chat_id, texto)

    # ---------- util ----------
    @staticmethod
    def _lista(r):
        if r is None:
            return []
        if isinstance(r, list):
            return r
        if isinstance(r, dict):
            # convert_dataframe_to_dict às vezes devolve dict único
            return [r] if r else []
        return list(r)
