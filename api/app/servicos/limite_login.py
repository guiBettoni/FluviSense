"""Limite de tentativas de login (proteção contra força bruta).

Regra: depois de MAXIMO_ERROS senhas erradas para o mesmo e-mail, vindas do mesmo endereço,
dentro de JANELA, novas tentativas ficam bloqueadas por TEMPO_BLOQUEIO. Um login certo zera a contagem.

A contagem fica na memória do processo: é simples e suficiente para uma API com um só servidor.
Se a API for reiniciada, a contagem recomeça.
"""

import threading
import time
from dataclasses import dataclass, field

MAXIMO_ERROS = 5
JANELA = 15 * 60          # segundos em que os erros são somados
TEMPO_BLOQUEIO = 15 * 60  # segundos de bloqueio depois do limite


@dataclass
class _Tentativas:
    erros: list[float] = field(default_factory=list)
    bloqueado_ate: float = 0.0


_tentativas: dict[tuple[str, str], _Tentativas] = {}
_trava = threading.Lock()


def _agora() -> float:
    return time.monotonic()


def segundos_bloqueado(email: str, endereco: str) -> int:
    """Quantos segundos faltam para liberar; 0 se não estiver bloqueado."""
    with _trava:
        registro = _tentativas.get((email, endereco))
        if not registro:
            return 0
        restante = registro.bloqueado_ate - _agora()
        return max(0, int(restante) + 1) if restante > 0 else 0


def registrar_erro(email: str, endereco: str) -> None:
    agora = _agora()
    with _trava:
        registro = _tentativas.setdefault((email, endereco), _Tentativas())
        registro.erros = [momento for momento in registro.erros if agora - momento < JANELA]
        registro.erros.append(agora)
        if len(registro.erros) >= MAXIMO_ERROS:
            registro.bloqueado_ate = agora + TEMPO_BLOQUEIO
            registro.erros.clear()


def registrar_acerto(email: str, endereco: str) -> None:
    with _trava:
        _tentativas.pop((email, endereco), None)


def limpar() -> None:
    """Usado pelos testes."""
    with _trava:
        _tentativas.clear()
