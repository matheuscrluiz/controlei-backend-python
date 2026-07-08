import os
from flask import jsonify, request
from flask_restx import Resource
from flask_restx.namespace import Namespace
from controlei.util.util import get_dict_retorno_endpoint
from ...util.constants import MSG_SUCESSO, TIP_RETORNO_SUCESS
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
        msg = update.get('message') or update.get('edited_message') or {}
        texto = (msg.get('text') or '').strip()
        chat = msg.get('chat') or {}
        chat_id = chat.get('id')

        # Só nos interessa o /start <token> do deep link de vínculo.
        if chat_id and texto.startswith('/start'):
            partes = texto.split(maxsplit=1)
            token = partes[1].strip() if len(partes) > 1 else None
            if token:
                user_f().processar_start_telegram(token, chat_id)
            # /start sem token: ignora silenciosamente (a resposta de
            # orientação fica a cargo do processar quando há token inválido)

        # Sempre 200: o Telegram reenvia updates que não recebem 2xx,
        # e não queremos loop de reentrega.
        return jsonify(
            get_dict_retorno_endpoint(
                TIP_RETORNO_SUCESS, MSG_SUCESSO, None)
        )
