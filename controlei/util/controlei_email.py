"""
Envio de e-mail transacional via Gmail SMTP (0800: stdlib smtplib, sem SDK,
sem domínio próprio — entrega pra QUALQUER destinatário).

Pré-requisitos na conta Google (uma vez):
  1) Ativar verificação em duas etapas (2FA).
  2) Gerar uma "Senha de app" (App Password) de 16 caracteres.

Config por variáveis de ambiente:
  GMAIL_USER          -> seu endereço Gmail (ex.: voce@gmail.com)
  GMAIL_APP_PASSWORD  -> a senha de app de 16 caracteres (pode colar com
                         espaços; eles são removidos)
  EMAIL_FROM_NAME     -> nome exibido do remetente (default 'Controlei')
  APP_URL             -> URL do app p/ o botão do e-mail (opcional)

enviar_email() NUNCA levanta exceção: retorna True/False, pra não derrubar
o cron caso o envio falhe.
"""
import os
import ssl
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # SSL

# Paleta Controlei
NAVY = "#001c43"
TEAL = "#0FA088"
INK = "#12241f"
MUTED = "#5e746c"
BG = "#eff4f2"


def enviar_email(destino: str, assunto: str, html: str) -> bool:
    usuario = os.environ.get("GMAIL_USER")
    senha = os.environ.get("GMAIL_APP_PASSWORD")
    nome_exib = os.environ.get("EMAIL_FROM_NAME", "Controlei")

    if not usuario or not senha or not destino:
        return False

    senha = senha.replace(" ", "")  # app password costuma vir com espaços

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = f"{nome_exib} <{usuario}>"
    msg["To"] = destino
    msg.set_content(
        "Este aviso do Controlei precisa de um cliente com suporte a HTML.")
    msg.add_alternative(html, subtype="html")

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT, context=contexto, timeout=20) as smtp:
            smtp.login(usuario, senha)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def render_email(
        titulo: str,
        subtitulo: str,
        linhas: list,
        cta_texto: str = None) -> str:
    """Template base único. `linhas` = lista de (label, valor)."""
    app_url = os.environ.get("APP_URL")

    linhas_html = "".join(
        f"""
        <tr>
          <td style="padding:6px 0;color:{MUTED};font-size:14px;">{lbl}</td>
          <td style="padding:6px 0;color:{INK};font-size:14px;
                     font-weight:700;text-align:right;">{val}</td>
        </tr>
        """
        for (lbl, val) in linhas
    )

    botao = ""
    if cta_texto and app_url:
        botao = f"""
        <tr><td style="padding-top:22px;">
          <a href="{app_url}" style="display:inline-block;background:{TEAL};
             color:#fff;text-decoration:none;font-weight:700;font-size:14px;
             padding:12px 22px;border-radius:10px;">{cta_texto}</a>
        </td></tr>
        """

    return f"""<!doctype html>
<html><body style="margin:0;background:{BG};
  font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:{BG};padding:24px 0;">
    <tr><td align="center">
      <table role="presentation" width="480" cellpadding="0" cellspacing="0"
             style="max-width:480px;width:100%;background:#fff;
                    border-radius:16px;overflow:hidden;
                    border:1px solid #e3ede8;">
        <tr><td style="background:{NAVY};padding:18px 24px;">
          <span style="color:#fff;font-size:18px;font-weight:800;
                       letter-spacing:-.02em;">Controlei</span>
        </td></tr>
        <tr><td style="padding:24px;">
          <div style="color:{INK};font-size:20px;font-weight:800;
                      margin-bottom:6px;">{titulo}</div>
          <div style="color:{MUTED};font-size:14px;margin-bottom:18px;">
            {subtitulo}</div>
          <table role="presentation" width="100%" cellpadding="0"
                 cellspacing="0"
                 style="border-top:1px solid #eaf1ed;
                        border-bottom:1px solid #eaf1ed;padding:4px 0;">
            {linhas_html}
          </table>
          <table role="presentation" cellpadding="0" cellspacing="0">
            {botao}
          </table>
        </td></tr>
        <tr><td style="padding:16px 24px;border-top:1px solid #eaf1ed;
                       color:{MUTED};font-size:12px;">
          Você recebe este aviso porque tem faturas no Controlei.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
