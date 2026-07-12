"""
Tokens de sessão (JWT HS256) com stdlib pura — sem dependência nova.

Config por variável de ambiente:
  JWT_SECRET -> segredo de assinatura (OBRIGATÓRIO; gere algo longo e
                aleatório, ex.: `openssl rand -hex 32`)

Regras:
  - gerar_token() levanta erro claro se JWT_SECRET não estiver configurado
    (melhor falhar visível no login do que emitir token inseguro).
  - validar_token() é fail-closed: qualquer problema (sem secret, assinatura
    errada, expirado, malformado) retorna None -> requisição negada.
"""
import os
import hmac
import json
import time
import base64
import hashlib

VALIDADE_HORAS_PADRAO = 24


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def gerar_token(id_usuario, horas: int = VALIDADE_HORAS_PADRAO) -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET não configurado no ambiente do backend")

    header = _b64e(json.dumps(
        {"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64e(json.dumps({
        "sub": str(id_usuario),
        "iat": int(time.time()),
        "exp": int(time.time()) + horas * 3600,
    }, separators=(",", ":")).encode())

    msg = f"{header}.{payload}".encode()
    assinatura = _b64e(
        hmac.new(secret.encode(), msg, hashlib.sha256).digest())

    return f"{header}.{payload}.{assinatura}"


def validar_token(token: str):
    """Retorna o id_usuario (int) se o token é válido; senão None."""
    secret = os.environ.get("JWT_SECRET")
    if not secret or not token:
        return None

    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        msg = f"{header_b64}.{payload_b64}".encode()
        esperada = hmac.new(secret.encode(), msg, hashlib.sha256).digest()

        if not hmac.compare_digest(esperada, _b64d(sig_b64)):
            return None

        payload = json.loads(_b64d(payload_b64))
        if int(payload.get("exp", 0)) < time.time():
            return None

        return int(payload["sub"])

    except Exception:
        return None
