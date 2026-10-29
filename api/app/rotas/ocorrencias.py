from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.dependencias import exigir_operador, ponto_ou_404
from app.esquemas import NovaOcorrencia, OcorrenciaSaida
from app.modelos import Ocorrencia, PontoMonitoramento, Usuario
from app.servicos import registrar_auditoria
from app.servicos.medicoes import em_utc, ocorrencia_aberta


roteador = APIRouter(tags=["ocorrências manuais"])


def ocorrencia_saida(ocorrencia: Ocorrencia, ponto: PontoMonitoramento) -> OcorrenciaSaida:
    return OcorrenciaSaida(
        id=ocorrencia.id,
        ponto_id=ponto.id,
        ponto_codigo=ponto.codigo,
        ponto_nome=ponto.nome,
        classificacao=ocorrencia.classificacao,
        motivo=ocorrencia.motivo,
        aberta_por=ocorrencia.aberta_por,
        aberta_em=em_utc(ocorrencia.aberta_em),
        encerrada_em=em_utc(ocorrencia.encerrada_em),
        encerrada_por=ocorrencia.encerrada_por,
    )


@roteador.get("/ocorrencias", response_model=list[OcorrenciaSaida])
def listar_ocorrencias(
    situacao: Literal["abertas", "todas"] = "abertas",
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    consulta = select(Ocorrencia, PontoMonitoramento).join(PontoMonitoramento, PontoMonitoramento.id == Ocorrencia.ponto_id)
    if situacao == "abertas":
        consulta = consulta.where(Ocorrencia.encerrada_em.is_(None))
    linhas = sessao.execute(consulta.order_by(Ocorrencia.id.desc()).limit(300)).all()
    return [ocorrencia_saida(ocorrencia, ponto) for ocorrencia, ponto in linhas]


@roteador.post("/pontos/{ponto_id}/ocorrencias", response_model=OcorrenciaSaida, status_code=status.HTTP_201_CREATED)
def abrir_ocorrencia(
    ponto_id: int,
    dados: NovaOcorrencia,
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    """O operador registra uma observação de campo que prevalece sobre as medições reais até ser encerrada."""
    ponto = ponto_ou_404(sessao, ponto_id)
    if ocorrencia_aberta(sessao, ponto.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este ponto já tem uma ocorrência aberta.")
    ocorrencia = Ocorrencia(
        ponto_id=ponto.id,
        classificacao=dados.classificacao,
        motivo=dados.motivo,
        aberta_por=operador.email,
        aberta_em=datetime.now(timezone.utc),
    )
    sessao.add(ocorrencia)
    sessao.flush()
    registrar_auditoria(
        sessao, operador.email, "OCORRENCIA_ABERTA", ponto.codigo,
        {"classificacao": ocorrencia.classificacao, "motivo": ocorrencia.motivo},
    )
    sessao.commit()
    return ocorrencia_saida(ocorrencia, ponto)


@roteador.put("/ocorrencias/{ocorrencia_id}/encerrar", response_model=OcorrenciaSaida)
def encerrar_ocorrencia(ocorrencia_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    ocorrencia = sessao.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    if ocorrencia.encerrada_em is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A ocorrência já foi encerrada.")
    ponto = ponto_ou_404(sessao, ocorrencia.ponto_id)
    ocorrencia.encerrada_em = datetime.now(timezone.utc)
    ocorrencia.encerrada_por = operador.email
    registrar_auditoria(sessao, operador.email, "OCORRENCIA_ENCERRADA", ponto.codigo, {"ocorrencia": ocorrencia.id})
    sessao.commit()
    return ocorrencia_saida(ocorrencia, ponto)
