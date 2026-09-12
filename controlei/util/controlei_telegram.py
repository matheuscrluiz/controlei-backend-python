"""
Envio de notificações via Telegram Bot API (0800: stdlib urllib).

Config por variáveis de ambiente:
  TELEGRAM_BOT_TOKEN      -> token do bot (do @BotFather)
  TELEGRAM_BOT_USERNAME   -> username do bot SEM @ (ex.: controlei_bot),
                             usado no deep link de vínculo
  TELEGRAM_WEBHOOK_SECRET -> segredo do webhook (o mesmo passado ao
                             setWebhook em secret_token)

enviar_telegram() NUNCA levanta exceção: retorna True/False.
"""
import os
import json
import urllib.request
import urllib.parse

API_BASE = "https://api.telegram.org"


def _url(metodo: str) -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    return f"{API_BASE}/bot{token}/{metodo}"


def enviar_telegram(chat_id: str, texto: str, botoes=None) -> bool:
    """Envia mensagem (HTML) pro chat. True/False, nunca levanta.

    botoes: lista de linhas; cada linha é lista de (rotulo, callback_data).
        Ex.: [[("Desfazer", "undo:123")], [("Nubank", "dest:conta:4"),
              ("Itaú", "dest:conta:7")]]
    callback_data tem limite de 64 bytes no Telegram — manter curto.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or not chat_id:
        return False

    payload = {
        "chat_id": str(chat_id),
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if botoes:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": rotulo, "callback_data": data}
                    for rotulo, data in linha]
                for linha in botoes
            ]
        }
    corpo = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        _url("sendMessage"),
        data=corpo,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def responder_callback(callback_id: str, texto: str = None) -> bool:
    """Confirma o clique num botão (o Telegram exige, senão o botão fica
    'carregando'). texto opcional aparece como toast pro usuário."""
    payload = {"callback_query_id": callback_id}
    if texto:
        payload["text"] = texto
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _url("answerCallbackQuery"), data=corpo, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def editar_mensagem(chat_id: str, message_id: int, texto: str) -> bool:
    """Edita uma mensagem já enviada (remove os botões e atualiza o texto —
    usado após Desfazer/escolha, pra não deixar botão 'vivo' de algo que
    já aconteceu)."""
    corpo = json.dumps({
        "chat_id": str(chat_id),
        "message_id": message_id,
        "text": texto,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(
        _url("editMessageText"), data=corpo, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def montar_link_vinculo(token_vinculo: str) -> str:
    """Deep link t.me pro usuário vincular a conta (clica -> /start token)."""
    username = os.environ.get("TELEGRAM_BOT_USERNAME", "")
    return f"https://t.me/{username}?start={urllib.parse.quote(token_vinculo)}"


def render_telegram(
        titulo: str,
        subtitulo: str,
        linhas: list,
        emoji: str = "💳") -> str:
    """Mensagem compacta em HTML do Telegram. `linhas` = [(label, valor)]."""
    app_url = os.environ.get("APP_URL")

    partes = [f"{emoji} <b>{titulo}</b>", subtitulo, ""]
    for (lbl, val) in linhas:
        partes.append(f"<b>{lbl}:</b> {val}")
    if app_url:
        partes.append("")
        partes.append(f'<a href="{app_url}">Abrir o Controlei</a>')
    return "\n".join(partes)
