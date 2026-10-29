"""Todas as rotas ficam sob /api."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.rotas import auditoria, autenticacao, medicoes, ocorrencias, pontos


roteador = APIRouter(prefix="/api")


@roteador.get("/saude")
def saude(sessao: Session = Depends(obter_sessao)):
    """Confere se a API está no ar e consegue falar com o banco."""
    sessao.execute(text("select 1"))
    return {"situacao": "ok", "banco": sessao.get_bind().dialect.name}


roteador.include_router(autenticacao.roteador)
roteador.include_router(pontos.roteador)
roteador.include_router(medicoes.roteador)
roteador.include_router(ocorrencias.roteador)
roteador.include_router(auditoria.roteador)
