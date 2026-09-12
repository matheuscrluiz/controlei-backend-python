import calendar
from datetime import date, datetime
from decimal import Decimal
from ...util.exceptions import FacadeException
from ...util.controlei_telegram import enviar_telegram, render_telegram
from ...util.controlei_email import enviar_email, render_email
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
        O GATILHO (quando chamar isto) fica a cargo do job/preguiçoso;
          aqui só a
        materialização.
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

    def _dados_despacho(self, id_usuario):
        """E-mail/Telegram + prefs do usuário (lidos direto: o
        get_preferencias não expõe o chat_id)."""
        import pandas as pd
        try:
            df = pd.read_sql(sql="""
                SELECT email, notif_email_ativo, notif_email_destino,
                       notif_telegram_ativo, telegram_chat_id
                FROM usuario WHERE id_usuario = %(u)s
            """, con=self.dao.get_connection(), params={'u': id_usuario})
            r = self.dao.convert_dataframe_to_dict(df)
            return r[0] if r else None
        except Exception:
            return None

    def _notificar_geradas(self, id_usuario, itens) -> bool:
        """Avisa por e-mail/Telegram (conforme prefs) o que foi lançado hoje.
        Fixas: informa. Variáveis: pede o valor."""
        prefs = self._dados_despacho(id_usuario)
        if not prefs:
            return False

        fixas = [g for g in itens if not g.get('variavel')]
        variaveis = [g for g in itens if g.get('variavel')]

        def _brl(v):
            v = float(v or 0)
            return "R$ " + f"{v:,.2f}".replace(",", "X").replace(
                ".", ",").replace("X", ".")

        linhas = []
        for g in fixas:
            sinal = '−' if g['natureza'] == 'despesa' else '+'
            linhas.append((g['descricao'], f"{sinal} {_brl(g['valor'])}"))
        for g in variaveis:
            linhas.append((g['descricao'], "quanto veio?"))

        n = len(itens)
        titulo = "Contas fixas de hoje" if n > 1 else "Conta fixa de hoje"
        if variaveis and not fixas:
            sub = ("Chegou a hora de informar o valor de "
                   + (f"{len(variaveis)} contas" if len(variaveis) > 1
                      else f"'{variaveis[0]['descricao']}'") + ".")
        elif variaveis:
            sub = (f"{len(fixas)} lançada(s) automaticamente e "
                   f"{len(variaveis)} aguardando o valor.")
        else:
            sub = f"{n} lançada(s) automaticamente no seu extrato."

        dica_tg = (
            "\n\n💬 Pra confirmar uma variável, responda só o valor: <b>187,40</b>"
            if variaveis else "")
        texto_tg = render_telegram(titulo, sub, linhas, emoji="🔁") + dica_tg
        html = render_email(titulo, sub, linhas, "Ver no Controlei",
                            etiqueta="Recorrência", acento="#0FA088")

        ok = False
        email = prefs.get('notif_email_destino') or prefs.get('email')
        if prefs.get('notif_email_ativo') and email:
            ok = enviar_email(email, f"{titulo} — Controlei", html) or ok
        chat_id = prefs.get('telegram_chat_id')
        if prefs.get('notif_telegram_ativo') and chat_id:
            ok = enviar_telegram(str(chat_id), texto_tg) or ok
        return ok

    def gerar_mes_todos(self):
        """Gera a ocorrência do mês para TODAS as recorrências ativas
        (de todos os usuários). Idempotente: o que já existe é ignorado.
        Pensado para ser chamado por um job/cron."""
        rotina = 'gerar_mes_todos'

        try:
            ativas = self.dao.get_recorrencia(ativa=True)
            geradas = 0
            puladas = 0
            erros = 0

            por_usuario = {}   # id_usuario -> lista do que foi gerado
            for r in ativas:
                try:
                    self._ultimo_gerado = None
                    res = self.gerar_ocorrencia(r['id_recorrencia'])
                    if isinstance(res, dict) and res.get('gerado') is False:
                        puladas += 1
                    else:
                        geradas += 1
                        g = getattr(self, '_ultimo_gerado', None)
                        if g and g.get('id_usuario'):
                            por_usuario.setdefault(
                                g['id_usuario'], []).append(g)
                except Exception:
                    erros += 1

            # ---- NOTIFICAÇÃO: uma mensagem por usuário com o que caiu hoje
            # Sem isso a recorrência é invisível: gera no extrato e ninguém vê.
            # Variáveis pedem o valor — e o bot do Telegram aceita a resposta
            # ("187,40") como confirmação.
            notificados = 0
            for id_usuario, itens in por_usuario.items():
                try:
                    if self._notificar_geradas(id_usuario, itens):
                        notificados += 1
                except Exception:
                    pass

            return {
                'total': len(ativas),
                'geradas': geradas,
                'puladas': puladas,
                'erros': erros,
                'usuarios_notificados': notificados,
            }

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
