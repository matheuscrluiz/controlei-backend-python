"""
Rate limit simples em memória (janela deslizante) — sem dependência nova.

Uso: proteger o /login contra força bruta. Adequado a um processo único
(caso do Render); se um dia houver múltiplas instâncias, trocar por um
armazenamento compartilhado (ex.: Redis).
"""
import time
import threading

_lock = threading.Lock()
_tentativas = {}  # chave -> [timestamps]

_MAX_CHAVES = 10000  # teto de memória: limpa tudo se estourar


def permitido(chave: str, maximo: int = 5, janela_seg: int = 60) -> bool:
    """True se a chave ainda tem cota na janela; registra a tentativa."""
    agora = time.time()
    corte = agora - janela_seg

    with _lock:
        if len(_tentativas) > _MAX_CHAVES:
            _tentativas.clear()

        registros = [t for t in _tentativas.get(chave, []) if t > corte]
        if len(registros) >= maximo:
            _tentativas[chave] = registros
            return False

        registros.append(agora)
        _tentativas[chave] = registros
        return True
