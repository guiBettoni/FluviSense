"""Regras do sistema que não dependem de HTTP."""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.modelos import EventoAuditoria


def registrar_auditoria(sessao: Session, autor: str, acao: str, entidade: str, detalhes: Any = None) -> None:
    """Registra uma alteração importante. Não grave dados pessoais em `detalhes`."""
    if detalhes is not None and not isinstance(detalhes, str):
        detalhes = json.dumps(detalhes, ensure_ascii=False, sort_keys=True, default=str)
    sessao.add(EventoAuditoria(autor=autor, acao=acao, entidade=entidade, detalhes=detalhes))
