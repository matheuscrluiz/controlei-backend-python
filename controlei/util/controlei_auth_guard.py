"""
Guarda global de autenticação/autorização da API (registrado no blueprint).

Padrão: o blueprint cuida só da fiação (namespaces, handlers) e delega a
segurança para cá via registrar_guarda(bp, prefixo). Toda rota nasce
protegida por padrão; o que é público está declarado explicitamente em
ROTAS_PUBLICAS.

Camadas:
  1) Autenticação — exige Authorization: Bearer <token> válido (JWT, 24h).
  2) Autorização (anti-IDOR) — o id_usuario que vale é o do token; um
     id_usuario diferente na URL, query ou corpo é negado com 403.
"""
from flask import request, g, jsonify

from .util import get_dict_retorno_endpoint
from .constants import TIP_RETORNO_ERROR
from .controlei_jwt import validar_token, validar_token_servico
from .controlei_rate_limit import permitido

# Rotas públicas (comparadas por sufixo do path). As de cron e o webhook
# do Telegram validam o próprio segredo dentro da rota
# (X-Cron-Secret / X-Telegram-Bot-Api-Secret-Token).
ROTAS_PUBLICAS = (
    '/login',
    '/telegram/webhook',
    '/fechar-automatico',
    '/notificar',
    '/gerar-todas',
    '/swagger.json',
)


def _negar(mensagem: str, status: int):
    resposta = jsonify(
        get_dict_retorno_endpoint(TIP_RETORNO_ERROR, mensagem, None))
    resposta.status_code = status
    return resposta


def _eh_rota_publica(prefixo: str) -> bool:
    # Preflight CORS passa sempre (o browser não manda Authorization aqui).
    if request.method == 'OPTIONS':
        return True

    # Swagger UI (a raiz do prefixo) é pública; os dados continuam
    # protegidos — testar rotas pelo Swagger exige o Authorize (Bearer).
    if request.path.rstrip('/') == prefixo.rstrip('/'):
        return True

    path = request.path.rstrip('/')
    return any(path.endswith(sufixo) for sufixo in ROTAS_PUBLICAS)


def _autenticar():
    """Valida o Bearer e devolve o id do usuário do token (ou None)."""
    auth = request.headers.get('Authorization', '')
    token = auth[7:].strip() if auth.startswith('Bearer ') else None
    return validar_token(token)


def _autorizar(id_usuario_token: int):
    """Anti-IDOR: nega id_usuario diferente do token, onde quer que venha.
    Retorna uma resposta de negação ou None (autorizado)."""
    candidatos = []
    if request.view_args and 'id_usuario' in request.view_args:
        candidatos.append(request.view_args.get('id_usuario'))
    if 'id_usuario' in request.args:
        candidatos.append(request.args.get('id_usuario'))
    corpo = request.get_json(silent=True)
    if isinstance(corpo, dict) and 'id_usuario' in corpo:
        candidatos.append(corpo.get('id_usuario'))

    for candidato in candidatos:
        try:
            if candidato is not None and int(candidato) != id_usuario_token:
                return _negar('Acesso negado: dados de outro usuário', 403)
        except (TypeError, ValueError):
            return _negar('Identificador de usuário inválido', 403)

    return None


def _coletar_ids_de_recurso():
    """Junta todos os parâmetros id_<recurso> presentes na requisição
    (query, path e corpo), exceto id_usuario (tratado à parte)."""
    achados = {}

    fontes = []
    if request.view_args:
        fontes.append(request.view_args)
    fontes.append(request.args)
    corpo = request.get_json(silent=True)
    if isinstance(corpo, dict):
        fontes.append(corpo)

    for fonte in fontes:
        for nome, valor in fonte.items():
            if (nome.startswith('id_') and nome != 'id_usuario'
                    and valor is not None):
                achados.setdefault(nome, valor)

    return achados


def _autorizar_recursos(id_usuario_token: int):
    """Anti-IDOR por RECURSO: cada id_<recurso> presente na requisição
    precisa pertencer ao usuário do token (ou ser global, dono NULL).
    Recurso inexistente passa — a rota devolve o 'não encontrado' natural."""
    ids = _coletar_ids_de_recurso()
    if not ids:
        return None

    # Import tardio: evita ciclo util -> model -> util na carga do app.
    from ..model.dao.controlei_posse_dao import (
        ControleiPosseDAO, RESOLVEDORES, NAO_ENCONTRADO)

    conhecidos = {n: v for n, v in ids.items() if n in RESOLVEDORES}
    if not conhecidos:
        return None

    dao = ControleiPosseDAO()
    for nome, valor in conhecidos.items():
        try:
            valor_int = int(valor)
        except (TypeError, ValueError):
            return _negar(f'Identificador inválido: {nome}', 403)

        dono = dao.obter_dono(nome, valor_int)
        if dono is NAO_ENCONTRADO or dono is None:
            continue  # inexistente (rota trata) ou recurso global
        if dono != id_usuario_token:
            return _negar('Acesso negado: recurso de outro usuário', 403)

    return None


def _limitar_login():
    """Força bruta no /login: 5 tentativas por IP por minuto."""
    ip = (request.headers.get('X-Forwarded-For', '')
          .split(',')[0].strip() or request.remote_addr or 'desconhecido')
    if not permitido(f'login:{ip}', maximo=5, janela_seg=60):
        return _negar(
            'Muitas tentativas de login. Aguarde um minuto.', 429)
    return None


def registrar_guarda(bp, prefixo: str):
    """Liga o guarda no blueprint: bp.before_request roda isto em toda
    requisição, antes de qualquer rota."""

    @bp.before_request
    def handler_auth_guard():
        # Login é público, mas com limite de tentativas (anti força bruta).
        if request.method == 'POST' and \
                request.path.rstrip('/').endswith('/login'):
            return _limitar_login()

        if _eh_rota_publica(prefixo):
            return None

        # Token de SERVIÇO (Power BI): leitor universal, somente GET.
        # Reconhecido antes do fluxo normal; quando presente e válido,
        # libera qualquer id_usuario mas restringe a métodos de leitura.
        auth = request.headers.get('Authorization', '')
        token_bruto = auth[7:].strip() if auth.startswith('Bearer ') else None
        if token_bruto and validar_token_servico(token_bruto):
            if request.method != 'GET':
                return _negar(
                    'Token de serviço permite apenas leitura (GET)', 403)
            # Leitura liberada para qualquer usuário: pula o anti-IDOR.
            g.token_servico = True
            return None

        id_usuario_token = _autenticar()
        if not id_usuario_token:
            return _negar('Não autorizado: faça login novamente', 401)

        # Disponível para as rotas via flask.g (quem está chamando).
        g.id_usuario_token = id_usuario_token

        negacao = _autorizar(id_usuario_token)
        if negacao is not None:
            return negacao

        return _autorizar_recursos(id_usuario_token)
