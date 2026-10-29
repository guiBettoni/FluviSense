import hashlib
import hmac
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.dependencias import exigir_operador, ponto_ou_404
from app.esquemas import MedicaoDoSensor, MedicaoSaida, NovaMedicao, NovaSimulacao, SimulacaoSaida
from app.modelos import Medicao, PontoMonitoramento, Usuario
from app.servicos import registrar_auditoria
from app.servicos.medicoes import (
    ORIGENS_REAIS,
    ORIGENS_SIMULADAS,
    agora_utc,
    conferir_horario,
    em_utc,
    registrar_medicao,
)
from app.servicos.simulacao import gerar_serie


roteador = APIRouter(tags=["medições"])


def medicao_saida(medicao: Medicao) -> MedicaoSaida:
    return MedicaoSaida(
        id=medicao.id,
        ponto_id=medicao.ponto_id,
        distancia_cm=float(medicao.distancia_cm),
        unidade=medicao.unidade,
        origem=medicao.origem,
        medida_em=em_utc(medicao.medida_em),
        recebida_em=em_utc(medicao.recebida_em),
        validade=medicao.validade,
        motivo_validade=medicao.motivo_validade,
        referencia_cm=None if medicao.referencia_cm is None else float(medicao.referencia_cm),
        classificacao=medicao.classificacao,
        registrada_por=medicao.registrada_por,
    )


def horario_ou_422(valor: datetime | None) -> datetime:
    try:
        return conferir_horario(valor)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)) from None


def ponto_ativo_ou_400(sessao: Session, ponto_id: int) -> PontoMonitoramento:
    ponto = ponto_ou_404(sessao, ponto_id)
    if not ponto.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ponto desativado não recebe medições.")
    return ponto


@roteador.get("/pontos/{ponto_id}/medicoes", response_model=list[MedicaoSaida])
def listar_medicoes(
    ponto_id: int,
    modo: Literal["real", "simulada", "todas"] = "real",
    desde: datetime | None = None,
    ate: datetime | None = None,
    limite: int = Query(default=200, ge=1, le=2000),
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    ponto_ou_404(sessao, ponto_id)
    consulta = select(Medicao).where(Medicao.ponto_id == ponto_id)
    if modo == "real":
        consulta = consulta.where(Medicao.origem.in_(ORIGENS_REAIS))
    elif modo == "simulada":
        consulta = consulta.where(Medicao.origem.in_(ORIGENS_SIMULADAS))
    if desde:
        consulta = consulta.where(Medicao.medida_em >= em_utc(desde))
    if ate:
        consulta = consulta.where(Medicao.medida_em <= em_utc(ate))
    linhas = sessao.scalars(consulta.order_by(Medicao.medida_em.desc(), Medicao.id.desc()).limit(limite)).all()
    return [medicao_saida(linha) for linha in linhas]


@roteador.post("/pontos/{ponto_id}/medicoes", response_model=MedicaoSaida, status_code=status.HTTP_201_CREATED)
def criar_medicao(
    ponto_id: int,
    dados: NovaMedicao,
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    """Registro feito pelo operador: medição manual (real, lida em campo) ou uma medição simulada avulsa."""
    ponto = ponto_ativo_ou_400(sessao, ponto_id)
    medida_em = horario_ou_422(dados.medida_em)
    medicao = registrar_medicao(sessao, ponto, dados.distancia_cm, dados.origem, medida_em, operador.email)
    if dados.origem == "manual":
        registrar_auditoria(
            sessao,
            operador.email,
            "MEDICAO_MANUAL_REGISTRADA",
            ponto.codigo,
            {"distancia_cm": dados.distancia_cm, "validade": medicao.validade, "medida_em": medida_em.isoformat()},
        )
    sessao.commit()
    return medicao_saida(medicao)


@roteador.post("/pontos/{ponto_id}/simulacoes", response_model=SimulacaoSaida, status_code=status.HTTP_201_CREATED)
def criar_simulacao(
    ponto_id: int,
    dados: NovaSimulacao,
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    ponto = ponto_ativo_ou_400(sessao, ponto_id)
    try:
        serie = gerar_serie(
            dados.cenario,
            dados.distancia_inicial_cm,
            dados.variacao_cm,
            dados.quantidade,
            dados.intervalo_minutos,
            agora_utc(),
        )
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)) from None
    criadas = [
        registrar_medicao(sessao, ponto, distancia, "simulada", medida_em, operador.email)
        for medida_em, distancia in serie
    ]
    registrar_auditoria(sessao, operador.email, "SIMULACAO_GERADA", ponto.codigo, dados.model_dump())
    sessao.commit()
    return SimulacaoSaida(
        criadas=len(criadas),
        suspeitas=sum(1 for m in criadas if m.validade == "suspeita"),
        invalidas=sum(1 for m in criadas if m.validade == "invalida"),
        medicoes=[medicao_saida(m) for m in criadas],
    )


@roteador.delete("/pontos/{ponto_id}/medicoes/simuladas")
def apagar_simuladas(ponto_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    """Apaga só as medições simuladas do ponto. Medições reais nunca são apagadas pela API."""
    ponto = ponto_ou_404(sessao, ponto_id)
    resultado = sessao.execute(
        delete(Medicao).where(Medicao.ponto_id == ponto.id, Medicao.origem.in_(ORIGENS_SIMULADAS))
    )
    registrar_auditoria(sessao, operador.email, "SIMULACAO_LIMPA", ponto.codigo, {"medicoes_apagadas": resultado.rowcount})
    sessao.commit()
    return {"apagadas": resultado.rowcount}


@roteador.post("/sensor/medicoes", response_model=MedicaoSaida, status_code=status.HTTP_201_CREATED)
def medicao_do_sensor(
    dados: MedicaoDoSensor,
    chave_sensor: str | None = Header(default=None, alias="X-Chave-Sensor"),
    sessao: Session = Depends(obter_sessao),
):
    """Entrada para sensores reais. Exige a chave gerada para o ponto (cabeçalho X-Chave-Sensor)."""
    ponto = sessao.scalar(select(PontoMonitoramento).where(PontoMonitoramento.codigo == dados.codigo_ponto.upper()))
    chave_certa = (
        ponto is not None
        and ponto.hash_chave_sensor is not None
        and chave_sensor is not None
        and hmac.compare_digest(ponto.hash_chave_sensor, hashlib.sha256(chave_sensor.encode("utf-8")).hexdigest())
    )
    if not chave_certa:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ponto ou chave do sensor inválidos.")
    if not ponto.ativo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ponto desativado não recebe medições.")
    medida_em = horario_ou_422(dados.medida_em)
    medicao = registrar_medicao(sessao, ponto, dados.distancia_cm, "sensor", medida_em, None)
    sessao.commit()
    return medicao_saida(medicao)
