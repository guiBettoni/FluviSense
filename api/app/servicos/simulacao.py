"""Geração de séries simuladas de distância (sensor até a superfície da água)."""

import math
from datetime import datetime, timedelta


def gerar_serie(
    cenario: str,
    distancia_inicial_cm: float,
    variacao_cm: float,
    quantidade: int,
    intervalo_minutos: int,
    fim: datetime,
) -> list[tuple[datetime, float]]:
    """Retorna (horário, distância) em ordem cronológica, terminando em `fim`.

    subida: a água sobe, então a distância diminui do valor inicial até inicial - variação.
    descida: a água desce, então a distância aumenta do valor inicial até inicial + variação.
    oscilacao: a distância oscila em torno do valor inicial com amplitude variação / 2 (um ciclo completo).
    """
    valores: list[float] = []
    ultimo = quantidade - 1
    for i in range(quantidade):
        fracao = i / ultimo
        if cenario == "subida":
            valor = distancia_inicial_cm - variacao_cm * fracao
        elif cenario == "descida":
            valor = distancia_inicial_cm + variacao_cm * fracao
        elif cenario == "oscilacao":
            valor = distancia_inicial_cm + (variacao_cm / 2) * math.sin(2 * math.pi * fracao)
        else:
            raise ValueError("Cenário desconhecido.")
        valores.append(round(valor, 2))
    if min(valores) <= 0:
        raise ValueError("Com esses parâmetros a distância chegaria a zero ou menos. Reduza a variação.")
    horarios = [fim - timedelta(minutes=intervalo_minutos * (ultimo - i)) for i in range(quantidade)]
    return list(zip(horarios, valores))
