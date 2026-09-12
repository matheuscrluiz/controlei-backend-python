import os
from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
from ...model.facade.controlei_telegram_bot import ControleiTelegramBot
from ...model.facade.controlei_usuario_facade import (
    ControleiUserFacade as user_f
)

# ---------------------------->>
# NameSpace
# ---------------------------->>

api = Namespace('telegram',
                description='Webhook do bot do Telegram')


# ---------------------------->>
# Rotas
# ---------------------------->>


@api.route('/webhook')
class TelegramWebhook(Resource):
    def post(self):
        """Recebe updates do Telegram. Protegido pelo header
        X-Telegram-Bot-Api-Secret-Token == env TELEGRAM_WEBHOOK_SECRET
        (o mesmo secret_token passado ao setWebhook)."""
        segredo = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
        enviado = request.headers.get('X-Telegram-Bot-Api-Secret-Token')

        if not segredo or enviado != segredo:
            return {'erro': 'Não autorizado'}, 401

        update = request.get_json(silent=True) or {}

        # ---- clique em botão inline (Desfazer / escolha de destino) ----
        cb = update.get('callback_query')
        if cb:
            try:
                msg_cb = cb.get('message') or {}
                ControleiTelegramBot().tratar_callback(
                    chat_id=(msg_cb.get('chat') or {}).get('id'),
                    message_id=msg_cb.get('message_id'),
                    callback_id=cb.get('id'),
                    data=cb.get('data') or '')
            except Exception:
                pass  # nunca deixa o webhook falhar (Telegram reenviaria)
            return jsonify(get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None))

        msg = update.get('message') or update.get('edited_message') or {}
        texto = (msg.get('text') or '').strip()
        chat = msg.get('chat') or {}
        chat_id = chat.get('id')

        if chat_id and texto:
            if texto.startswith('/start'):
                # deep link de vínculo (fluxo já existente)
                partes = texto.split(maxsplit=1)
                token = partes[1].strip() if len(partes) > 1 else None
                if token:
                    user_f().processar_start_telegram(token, chat_id)
            else:
                # qualquer outra mensagem: o bot interpreta e registra
                try:
                    ControleiTelegramBot().tratar_mensagem(chat_id, texto)
                except Exception:
                    pass  # idem: webhook sempre 200

        # Sempre 200: o Telegram reenvia updates que não recebem 2xx,
        # e não queremos loop de reentrega.
        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
