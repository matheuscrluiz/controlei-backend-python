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
        cta_texto: str = None,
        etiqueta: str = None,
        acento: str = TEAL) -> str:
    """Template base único. `linhas` = lista de (label, valor).
    `etiqueta` = selo colorido no topo (ex.: 'Vencida'); `acento` = cor
    do selo/botão/faixa (coral, âmbar ou teal conforme o fluxo)."""
    app_url = os.environ.get("APP_URL")
    logo_url = os.environ.get("LOGO_URL")

    if logo_url:
        marca = (
            f'<img src="{logo_url}" alt="Controlei" height="26" '
            f'style="display:block;border:0;height:26px;">'
        )
    else:
        marca = (
            f'<span style="color:#fff;font-size:18px;font-weight:800;'
            f'letter-spacing:-.02em;">Controlei</span>'
        )

    selo = ""
    if etiqueta:
        selo = (
            f'<span style="display:inline-block;background:{acento};'
            f'color:#fff;font-size:11px;font-weight:800;text-transform:'
            f'uppercase;letter-spacing:.04em;padding:5px 10px;'
            f'border-radius:999px;margin-bottom:12px;">{etiqueta}</span>'
        )

    # Última linha (Total) recebe destaque maior.
    ult = len(linhas) - 1
    linhas_html = ""
    for i, (lbl, val) in enumerate(linhas):
        grande = i == ult
        cor_val = acento if grande else INK
        tam = "18px" if grande else "14px"
        borda = "" if grande else "border-bottom:1px solid #f0f5f2;"
        linhas_html += f"""
        <tr>
          <td style="padding:9px 0;color:{MUTED};font-size:14px;{borda}">
            {lbl}</td>
          <td style="padding:9px 0;color:{cor_val};font-size:{tam};
                     font-weight:800;text-align:right;{borda}">{val}</td>
        </tr>
        """

    botao = ""
    if cta_texto and app_url:
        botao = f"""
        <tr><td style="padding-top:24px;">
          <a href="{app_url}" style="display:inline-block;background:{acento};
             color:#fff;text-decoration:none;font-weight:700;font-size:14px;
             padding:13px 26px;border-radius:10px;">{cta_texto}</a>
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
        <tr><td style="background:{NAVY};padding:18px 24px;">{marca}</td></tr>
        <tr><td style="height:4px;background:{acento};line-height:4px;
                       font-size:0;">&nbsp;</td></tr>
        <tr><td style="padding:26px 24px 24px;">
          {selo}
          <div style="color:{INK};font-size:21px;font-weight:800;
                      margin-bottom:6px;line-height:1.25;">{titulo}</div>
          <div style="color:{MUTED};font-size:14px;margin-bottom:18px;
                      line-height:1.5;">{subtitulo}</div>
          <table role="presentation" width="100%" cellpadding="0"
                 cellspacing="0">
            {linhas_html}
          </table>
          <table role="presentation" cellpadding="0" cellspacing="0">
            {botao}
          </table>
        </td></tr>
        <tr><td style="padding:16px 24px;border-top:1px solid #eaf1ed;
                       color:{MUTED};font-size:12px;line-height:1.5;">
          Você recebe este aviso porque tem faturas no Controlei.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
