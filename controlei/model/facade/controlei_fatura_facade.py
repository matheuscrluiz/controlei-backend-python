import calendar
from datetime import date, datetime
from ...util.exceptions import FacadeException
from ...util.util import convert_unique_dic_to_arrayDict
from ...util.controlei_email import enviar_email, render_email
from ...util.controlei_telegram import enviar_telegram, render_telegram
from ..dao.controlei_fatura_dao import ControleiFaturaDAO
from ..dao.controlei_cartao_dao import ControleiCartaoDAO

STATUS_VALIDOS = ('aberta', 'fechada', 'paga')


def _data_no_mes(ano: int, mes: int, dia: int) -> date:
    """Monta a data no mês, limitando o dia ao último dia (ex.: 31 em fev)."""
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


def _proximo_mes(ano: int, mes: int):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


_MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
          'jul', 'ago', 'set', 'out', 'nov', 'dez']


def _para_date(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    s = str(valor).split('T')[0].split(' ')[0]
    for fmt in ('%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %Z', '%d/%m/%Y'):
        try:
            return datetime.strptime(str(valor), fmt).date()
        except ValueError:
            continue
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _fmt_data(valor) -> str:
    d = _para_date(valor)
    return d.strftime('%d/%m/%Y') if d else '—'


def _fmt_mes(valor) -> str:
    d = _para_date(valor)
    return f"{_MESES[d.month - 1]}/{d.year}" if d else '—'


def _fmt_moeda(v: float) -> str:
    s = f"{float(v):,.2f}"
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"


def _normalizar_competencia(competencia) -> date:
    """Aceita date ou string ('YYYY-MM' / 'YYYY-MM-DD') e devolve o 1º do mês."""
    if isinstance(competencia, date):
        return date(competencia.year, competencia.month, 1)
    texto = str(competencia).strip()
    for fmt in ('%Y-%m-%d', '%Y-%m'):
        try:
            d = datetime.strptime(texto, fmt).date()
            return date(d.year, d.month, 1)
        except ValueError:
            continue
    raise ValueError('Competência inválida (use YYYY-MM ou YYYY-MM-DD)')


class ControleiFaturaFacade():

    def __init__(self):
        """construtor da classe ControleiFaturaFacade"""
        self.dao = ControleiFaturaDAO()
        self.cartao_dao = ControleiCartaoDAO()

    def obter_fatura(
            self,
            id_fatura=None,
            id_cartao=None,
            status=None,
            competencia=None,
            id_usuario=None) -> dict:
        rotina = 'obter_fatura'

        try:
            if competencia:
                competencia = _normalizar_competencia(competencia)

            fatura = self.dao.get_fatura(
                id_fatura=id_fatura,
                id_cartao=id_cartao,
                status=status,
                competencia=competencia,
                id_usuario=id_usuario)
            return convert_unique_dic_to_arrayDict(fatura)

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_faturas_a_vencer(self, id_usuario, dias=7) -> dict:
        rotina = 'obter_faturas_a_vencer'

        try:
            d = int(dias) if dias is not None else 7
            return convert_unique_dic_to_arrayDict(
                self.dao.get_faturas_a_vencer(id_usuario=id_usuario, dias=d))

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def fechar_faturas_do_dia(self) -> dict:
        """Fecha (aberta -> fechada) as faturas cujo dia de fechamento já
        chegou. Idempotente: só toca em 'aberta'. Feito pra rodar no cron."""
        rotina = 'fechar_faturas_do_dia'

        try:
            ids = self.dao.get_ids_faturas_para_fechar()
            fechadas = 0
            for id_fatura in ids:
                self.dao.update_status_fatura(id_fatura, 'fechada')
                fechadas += 1
            if fechadas:
                self.dao.database_commit()
            return {'fechadas': fechadas}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def processar_notificacoes_faturas(self) -> dict:
        """Roda no cron diário. Decide e envia e-mails por fatura, com
        prioridade vencida > a vencer > fechada, e marca cada envio pra
        não repetir. Defaults: fechada 1x; a vencer em 3 e 1 dia;
        vencida re-avisa a cada 3 dias até pagar."""
        rotina = 'processar_notificacoes_faturas'

        try:
            faturas = self.dao.get_faturas_para_notificar()
            enviados = {'fechada': 0, 'avencer': 0, 'vencida': 0}

            def _despachar(f, assunto, html, texto_tg) -> bool:
                """Envia pelos canais ligados do usuário.
                Sucesso = pelo menos um canal entregou."""
                ok = False
                email = f.get('email_destino') or f.get('email_usuario')
                if f.get('notif_email_ativo') and email:
                    ok = enviar_email(email, assunto, html) or ok
                chat_id = f.get('telegram_chat_id')
                if f.get('notif_telegram_ativo') and chat_id:
                    ok = enviar_telegram(str(chat_id), texto_tg) or ok
                return ok

            for f in faturas:

                dias = f.get('dias_ate')
                dias = int(dias) if dias is not None else None
                status = f.get('status')
                total = float(f.get('total') or 0)
                nome = f.get('nome_usuario') or ''

                cartao = f.get('apelido_cartao') or 'Cartão'
                fim = f.get('ultimos4')
                if fim:
                    cartao = f"{cartao} ••{fim}"
                banco = f.get('apelido_conta')
                venc = _fmt_data(f.get('data_vencimento'))
                mes = _fmt_mes(f.get('competencia'))

                base_linhas = [('Cartão', cartao)]
                if banco:
                    base_linhas.append(('Conta', banco))
                base_linhas.append(('Competência', mes))
                base_linhas.append(('Vencimento', venc))
                base_linhas.append(('Total', _fmt_moeda(total)))

                # ---- VENCIDA (mais urgente) ----
                if dias is not None and dias < 0:
                    if not f.get('notif_vencida_ativa'):
                        continue
                    desde = f.get('dias_desde_vencida')
                    ja = f.get('notif_vencida_em')
                    reenviar = (ja is None) or (
                        desde is not None and int(desde) >= 3)
                    if reenviar:
                        atraso = abs(dias)
                        titulo = "Fatura vencida"
                        sub = (f"{nome}, sua fatura de {cartao} venceu há "
                               f"{atraso} dia{'s' if atraso > 1 else ''}.")
                        html = render_email(
                            titulo, sub, base_linhas, "Pagar agora",
                            etiqueta="Vencida", acento="#E15C6B")
                        texto_tg = render_telegram(
                            titulo, sub, base_linhas, emoji="🚨")
                        if _despachar(
                                f, f"{titulo} — {cartao}", html, texto_tg):
                            self.dao.marcar_notif(
                                f['id_fatura'], 'notif_vencida_em',
                                date.today())
                            enviados['vencida'] += 1
                    continue

                # ---- A VENCER (3 e 1 dia) ----
                if dias == 3 and not f.get('notif_avencer_3'):
                    if not f.get('notif_avencer_ativa'):
                        continue
                    titulo = "Fatura a vencer"
                    sub = f"{nome}, sua fatura de {cartao} vence em 3 dias."
                    html = render_email(
                        titulo, sub, base_linhas, "Pagar fatura",
                        etiqueta="Vence em 3 dias", acento="#E0A23C")
                    texto_tg = render_telegram(
                        titulo, sub, base_linhas, emoji="⏳")
                    if _despachar(f, f"{titulo} — {cartao}", html, texto_tg):
                        self.dao.marcar_notif(
                            f['id_fatura'], 'notif_avencer_3', True)
                        enviados['avencer'] += 1
                    continue

                if dias == 1 and not f.get('notif_avencer_1'):
                    if not f.get('notif_avencer_ativa'):
                        continue
                    titulo = "Fatura vence amanhã"
                    sub = f"{nome}, sua fatura de {cartao} vence amanhã."
                    html = render_email(
                        titulo, sub, base_linhas, "Pagar fatura",
                        etiqueta="Vence amanhã", acento="#E0A23C")
                    texto_tg = render_telegram(
                        titulo, sub, base_linhas, emoji="⏰")
                    if _despachar(f, f"{titulo} — {cartao}", html, texto_tg):
                        self.dao.marcar_notif(
                            f['id_fatura'], 'notif_avencer_1', True)
                        enviados['avencer'] += 1
                    continue

                # ---- FECHADA (uma vez) ----
                if status == 'fechada' and not f.get('notif_fechada'):
                    if not f.get('notif_fechada_ativa'):
                        continue
                    titulo = "Fatura fechada"
                    sub = (f"{nome}, sua fatura de {cartao} fechou. "
                           f"Vence em {venc}.")
                    html = render_email(
                        titulo, sub, base_linhas, "Ver fatura",
                        etiqueta="Fatura fechada", acento="#0FA088")
                    texto_tg = render_telegram(
                        titulo, sub, base_linhas, emoji="✅")
                    if _despachar(f, f"{titulo} — {cartao}", html, texto_tg):
                        self.dao.marcar_notif(
                            f['id_fatura'], 'notif_fechada', True)
                        enviados['fechada'] += 1
                    continue

            total_env = sum(enviados.values())
            if total_env:
                self.dao.database_commit()

            return {'enviados': total_env, 'detalhe': enviados}

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_ou_criar_fatura(self, id_cartao: int, competencia) -> dict:
        """
        Acha a fatura do cartão naquela competência (mês de referência) ou cria
        uma nova, calculando fechamento/vencimento a partir dos dias do cartão.
        É o método que o fluxo de compra/parcela usa pra alocar cada parcela.
        """
        rotina = 'obter_ou_criar_fatura'

        try:
            if not id_cartao:
                raise FacadeException(
                    __file__, rotina, 'ID do cartão é obrigatório')

            competencia = _normalizar_competencia(competencia)

            # Já existe a fatura desse mês? Retorna ela.
            existente = self.dao.get_fatura(
                id_cartao=id_cartao, competencia=competencia)
            if existente:
                return existente[0]

            # Não existe: precisa dos dias do cartão pra calcular as datas.
            cartao = self.cartao_dao.get_cartao(id_cartao=id_cartao)
            if not cartao:
                raise FacadeException(
                    __file__, rotina, 'Cartão não encontrado')
            cartao = cartao[0]

            dia_fechamento = cartao.get('dia_fechamento')
            dia_vencimento = cartao.get('dia_vencimento')
            if not dia_fechamento or not dia_vencimento:
                raise FacadeException(
                    __file__, rotina,
                    'Cartão sem dia de fechamento/vencimento (não é crédito?)')

            data_fechamento = _data_no_mes(
                competencia.year, competencia.month, int(dia_fechamento))

            # Vence depois de fechar: se o dia de vencimento é <= fechamento,
            # ele cai no mês seguinte.
            if int(dia_vencimento) <= int(dia_fechamento):
                vy, vm = _proximo_mes(competencia.year, competencia.month)
            else:
                vy, vm = competencia.year, competencia.month
            data_vencimento = _data_no_mes(vy, vm, int(dia_vencimento))

            id_fatura = self.dao.insert_fatura({
                'id_cartao': id_cartao,
                'competencia': competencia,
                'data_fechamento': data_fechamento,
                'data_vencimento': data_vencimento,
                'status': 'aberta',
            })
            self.dao.database_commit()

            return self.dao.get_fatura(id_fatura=id_fatura)[0]

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def obter_total_fatura(self, id_fatura: int):
        """Retorna o total a pagar da fatura (parcelas + itens)."""
        rotina = 'obter_total_fatura'

        try:
            resultado = self.dao.get_total(id_fatura)
            if not resultado:
                return 0
            return resultado[0].get('valor') or 0

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)

    def atualizar_status_fatura(self, id_fatura: int, status: str):
        """Primitiva de status (aberta/fechada/paga). O 'pagar fatura' completo
        — com a transferência que baixa o saldo — virá no fluxo de pagamento."""
        rotina = 'atualizar_status_fatura'

        try:
            if not id_fatura:
                raise FacadeException(
                    __file__, rotina, 'ID da fatura é obrigatório')

            status = (status or '').strip().lower()
            if status not in STATUS_VALIDOS:
                raise FacadeException(
                    __file__, rotina,
                    'Status inválido (use: aberta, fechada ou paga)')

            fatura = self.dao.get_fatura(id_fatura=id_fatura)
            if not fatura:
                raise FacadeException(
                    __file__, rotina, 'Fatura não encontrada')

            self.dao.update_status_fatura(id_fatura, status)
            self.dao.database_commit()

        except Exception as erro:
            raise FacadeException(__file__, rotina, erro)
