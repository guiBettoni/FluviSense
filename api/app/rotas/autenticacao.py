from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.dependencias import PERFIL_OPERADOR, exigir_operador
from app.esquemas import PedidoLogin, RespostaLogin, UsuarioSaida
from app.modelos import Usuario
from app.seguranca import conferir_senha, criar_token_acesso
from app.servicos import limite_login, registrar_auditoria


roteador = APIRouter(prefix="/autenticacao", tags=["autenticação"])


def usuario_saida(usuario: Usuario) -> UsuarioSaida:
    return UsuarioSaida(id=usuario.id, nome=usuario.nome, email=usuario.email, perfil=usuario.perfil)


@roteador.post("/login", response_model=RespostaLogin)
def entrar(dados: PedidoLogin, requisicao: Request, sessao: Session = Depends(obter_sessao)):
    endereco = requisicao.client.host if requisicao.client else "desconhecido"
    espera = limite_login.segundos_bloqueado(dados.email, endereco)
    if espera:
        minutos = max(1, -(-espera // 60))  # arredonda para cima
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas de login com senha errada. Tente de novo em {minutos} {'minuto' if minutos == 1 else 'minutos'}.",
            headers={"Retry-After": str(espera)},  # cabeçalho do padrão HTTP: segundos até liberar
        )
    usuario = sessao.scalar(
        select(Usuario).where(
            func.lower(Usuario.email) == dados.email,
            Usuario.perfil == PERFIL_OPERADOR,
            Usuario.ativo.is_(True),
        )
    )
    if not usuario or not conferir_senha(dados.senha, usuario.hash_senha):
        limite_login.registrar_erro(dados.email, endereco)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")
    limite_login.registrar_acerto(dados.email, endereco)
    usuario.ultimo_login_em = datetime.now(timezone.utc)
    registrar_auditoria(sessao, usuario.email, "LOGIN_OPERADOR", "acesso")
    sessao.commit()
    return RespostaLogin(token_acesso=criar_token_acesso(str(usuario.id), usuario.perfil), usuario=usuario_saida(usuario))


@roteador.get("/operador", response_model=UsuarioSaida)
def operador_logado(operador: Usuario = Depends(exigir_operador)):
    return usuario_saida(operador)
