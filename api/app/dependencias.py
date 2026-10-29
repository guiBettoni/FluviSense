"""Verificações usadas por várias rotas: operador logado e ponto existente."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.modelos import PontoMonitoramento, Usuario
from app.seguranca import ler_token_acesso


PERFIL_OPERADOR = "OPERADOR"

# Lê o cabeçalho "Authorization: Bearer <token>" (nomes definidos pelo padrão HTTP).
esquema_token = HTTPBearer(auto_error=False)


def exigir_operador(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema_token),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    if not credenciais:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação obrigatória.")
    conteudo = ler_token_acesso(credenciais.credentials)
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada.")
    if conteudo.get("perfil") != PERFIL_OPERADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao operador.")
    try:
        usuario_id = int(conteudo.get("sub", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.") from None
    usuario = sessao.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo or usuario.perfil != PERFIL_OPERADOR:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operador inativo ou inexistente.")
    return usuario


def ponto_ou_404(sessao: Session, ponto_id: int) -> PontoMonitoramento:
    ponto = sessao.get(PontoMonitoramento, ponto_id)
    if not ponto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ponto de monitoramento não encontrado.")
    return ponto
