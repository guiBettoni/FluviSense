from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.dependencias import exigir_operador
from app.esquemas import EventoAuditoriaSaida
from app.modelos import EventoAuditoria, Usuario
from app.servicos.medicoes import em_utc


roteador = APIRouter(tags=["auditoria"])


@roteador.get("/auditoria", response_model=list[EventoAuditoriaSaida])
def listar_auditoria(
    limite: int = Query(default=250, ge=1, le=1000),
    sessao: Session = Depends(obter_sessao),
    operador: Usuario = Depends(exigir_operador),
):
    eventos = sessao.scalars(select(EventoAuditoria).order_by(EventoAuditoria.id.desc()).limit(limite)).all()
    return [
        EventoAuditoriaSaida(
            id=evento.id,
            autor=evento.autor,
            acao=evento.acao,
            entidade=evento.entidade,
            detalhes=evento.detalhes,
            criado_em=em_utc(evento.criado_em),
        )
        for evento in eventos
    ]
