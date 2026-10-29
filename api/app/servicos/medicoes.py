"""Regras das medições: validade técnica, suspeita, classificação e situação atual do ponto.

A grandeza medida é a distância entre o sensor e a superfície da água (cm).
O sensor fica acima da água, então água subindo = distância diminuindo.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import Medicao, Ocorrencia, PontoMonitoramento


ORIGENS_REAIS = ("sensor", "manual")
ORIGENS_SIMULADAS = ("simulada",)
TAMANHO_REFERENCIA = 3
PROPORCAO_SALTO_PADRAO = 0.5  # 50%, herdado do antigo RNF08; cada ponto pode trocar por salto_maximo_cm.
TOLERANCIA_FUTURO = timedelta(minutes=5)


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def em_utc(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def origens_do_modo(modo: str) -> tuple[str, ...]:
    return ORIGENS_SIMULADAS if modo == "simulada" else ORIGENS_REAIS


def _numero(valor) -> float | None:
    return None if valor is None else float(valor)


def possui_criterios(ponto: PontoMonitoramento) -> bool:
    return ponto.distancia_atencao_cm is not None


def classificar(ponto: PontoMonitoramento, distancia_cm: float) -> str:
    """Compara a distância com os critérios configurados no ponto."""
    if not possui_criterios(ponto):
        return "sem_criterio"
    if distancia_cm <= float(ponto.distancia_critica_cm):
        return "vermelho"
    if distancia_cm <= float(ponto.distancia_alerta_cm):
        return "laranja"
    if distancia_cm <= float(ponto.distancia_atencao_cm):
        return "amarelo"
    return "verde"


@dataclass
class Avaliacao:
    validade: str
    motivo: str | None
    referencia_cm: float | None


def avaliar(sessao: Session, ponto: PontoMonitoramento, distancia_cm: float, origem: str, medida_em: datetime) -> Avaliacao:
    """Separa a validade técnica (invalida) da suspeita de variação brusca (suspeita).

    A referência é a mediana das 3 últimas medições não inválidas do mesmo fluxo (real ou simulado)
    anteriores a esta. Medições suspeitas entram na referência: assim um pico isolado é ignorado,
    mas uma mudança que se mantém por 3 leituras vira a nova referência.
    """
    if distancia_cm <= 0:
        return Avaliacao("invalida", "Distância menor ou igual a zero.", None)
    minima = _numero(ponto.distancia_minima_valida_cm)
    maxima = _numero(ponto.distancia_maxima_valida_cm)
    if minima is not None and distancia_cm < minima:
        return Avaliacao("invalida", f"Abaixo do mínimo técnico configurado ({minima:g} cm).", None)
    if maxima is not None and distancia_cm > maxima:
        return Avaliacao("invalida", f"Acima do máximo técnico configurado ({maxima:g} cm).", None)

    fluxo = ORIGENS_SIMULADAS if origem in ORIGENS_SIMULADAS else ORIGENS_REAIS
    anteriores = sessao.scalars(
        select(Medicao.distancia_cm)
        .where(
            Medicao.ponto_id == ponto.id,
            Medicao.origem.in_(fluxo),
            Medicao.validade != "invalida",
            Medicao.medida_em < medida_em,
        )
        .order_by(Medicao.medida_em.desc(), Medicao.id.desc())
        .limit(TAMANHO_REFERENCIA)
    ).all()
    if len(anteriores) < TAMANHO_REFERENCIA:
        return Avaliacao("valida", None, None)

    referencia = round(median(float(valor) for valor in anteriores), 2)
    limite = _numero(ponto.salto_maximo_cm)
    if limite is None:
        limite = referencia * PROPORCAO_SALTO_PADRAO
        texto_limite = f"{limite:.2f} cm (50% da referência)"
    else:
        texto_limite = f"{limite:g} cm (configurado no ponto)"
    variacao = abs(distancia_cm - referencia)
    if variacao > limite:
        return Avaliacao(
            "suspeita",
            f"Variação de {variacao:.2f} cm em relação à referência de {referencia:g} cm; limite {texto_limite}.",
            referencia,
        )
    return Avaliacao("valida", None, referencia)


def conferir_horario(medida_em: datetime | None) -> datetime:
    """Horário da medição em UTC. Sem horário, usa o horário de recebimento."""
    agora = agora_utc()
    if medida_em is None:
        return agora
    medida_em = em_utc(medida_em)
    if medida_em > agora + TOLERANCIA_FUTURO:
        raise ValueError("O horário da medição está no futuro.")
    return medida_em


def registrar_medicao(
    sessao: Session,
    ponto: PontoMonitoramento,
    distancia_cm: float,
    origem: str,
    medida_em: datetime,
    registrada_por: str | None,
) -> Medicao:
    avaliacao = avaliar(sessao, ponto, distancia_cm, origem, medida_em)
    classificacao = None if avaliacao.validade == "invalida" else classificar(ponto, distancia_cm)
    medicao = Medicao(
        ponto_id=ponto.id,
        distancia_cm=round(distancia_cm, 2),
        unidade="cm",
        origem=origem,
        medida_em=medida_em,
        recebida_em=agora_utc(),
        validade=avaliacao.validade,
        motivo_validade=avaliacao.motivo,
        referencia_cm=avaliacao.referencia_cm,
        classificacao=classificacao,
        registrada_por=registrada_por,
    )
    sessao.add(medicao)
    sessao.flush()
    return medicao


def ocorrencia_aberta(sessao: Session, ponto_id: int) -> Ocorrencia | None:
    return sessao.scalar(
        select(Ocorrencia)
        .where(Ocorrencia.ponto_id == ponto_id, Ocorrencia.encerrada_em.is_(None))
        .order_by(Ocorrencia.id.desc())
        .limit(1)
    )


def estado_do_ponto(sessao: Session, ponto: PontoMonitoramento, modo: str = "real", agora: datetime | None = None) -> dict:
    """Situação do ponto para um fluxo de dados (real ou simulado).

    `situacao` é o que deve ser exibido:
    - sem_dados: nenhuma medição aproveitável;
    - desatualizado: a última medição passou do prazo do ponto e não confirma a condição atual;
    - sem_criterio: há dado atual, mas o ponto não tem critérios configurados;
    - verde, amarelo, laranja, vermelho: classificação pelos critérios do ponto.
    Uma ocorrência manual aberta prevalece sobre as medições reais.
    """
    agora = agora or agora_utc()
    ultima = sessao.scalar(
        select(Medicao)
        .where(
            Medicao.ponto_id == ponto.id,
            Medicao.origem.in_(origens_do_modo(modo)),
            Medicao.validade != "invalida",
        )
        .order_by(Medicao.medida_em.desc(), Medicao.id.desc())
        .limit(1)
    )
    ultima_recebida = sessao.scalar(
        select(Medicao)
        .where(Medicao.ponto_id == ponto.id, Medicao.origem.in_(origens_do_modo(modo)))
        .order_by(Medicao.recebida_em.desc(), Medicao.id.desc())
        .limit(1)
    )
    ocorrencia = ocorrencia_aberta(sessao, ponto.id) if modo == "real" else None

    estado = {
        "modo": modo,
        "situacao": "sem_dados",
        "classificacao": None,
        "distancia_cm": None,
        "medida_em": None,
        "validade": None,
        "motivo_validade": None,
        "desatualizado": False,
        "ultima_recebida_invalida": bool(ultima_recebida and ultima_recebida.validade == "invalida"),
        "ocorrencia": None,
    }
    if ultima:
        medida_em = em_utc(ultima.medida_em)
        desatualizado = agora - medida_em > timedelta(minutes=ponto.minutos_para_desatualizar)
        classificacao = classificar(ponto, float(ultima.distancia_cm))
        estado.update(
            classificacao=classificacao,
            distancia_cm=float(ultima.distancia_cm),
            medida_em=medida_em,
            validade=ultima.validade,
            motivo_validade=ultima.motivo_validade,
            desatualizado=desatualizado,
            situacao="desatualizado" if desatualizado else classificacao,
        )
    if ocorrencia:
        estado["ocorrencia"] = {
            "id": ocorrencia.id,
            "classificacao": ocorrencia.classificacao,
            "motivo": ocorrencia.motivo,
            "aberta_em": em_utc(ocorrencia.aberta_em),
        }
        estado["situacao"] = ocorrencia.classificacao
    return estado
