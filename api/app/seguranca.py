"""Senhas e tokens de acesso do operador.

O token segue o formato JWT (padrão RFC 7519). Por isso as partes fixas do formato continuam com
os nomes do padrão: "alg" e "typ" no cabeçalho; "sub" (de quem é o token), "iat" (quando foi
emitido) e "exp" (quando expira) no conteúdo. O campo "perfil" é do próprio FluviSense.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


ALGORITMO_SENHA = "pbkdf2_sha256"
ITERACOES_SENHA = 210_000
ALGORITMO_JWT = "HS256"
TAMANHO_MINIMO_SEGREDO = 32


def gerar_hash_senha(senha: str) -> str:
    sal = secrets.token_urlsafe(24)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal.encode("utf-8"), ITERACOES_SENHA)
    return f"{ALGORITMO_SENHA}${ITERACOES_SENHA}${sal}${_b64(resumo)}"


def conferir_senha(senha: str, hash_senha: str) -> bool:
    try:
        algoritmo, iteracoes, sal, resumo_esperado = hash_senha.split("$", 3)
        if algoritmo != ALGORITMO_SENHA:
            return False
        resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal.encode("utf-8"), int(iteracoes))
        return hmac.compare_digest(_b64(resumo), resumo_esperado)
    except (AttributeError, TypeError, ValueError):
        return False


def criar_token_acesso(usuario_id: str, perfil: str) -> str:
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "480")))
    conteudo = {"sub": usuario_id, "perfil": perfil, "iat": int(agora.timestamp()), "exp": int(expira_em.timestamp())}
    cabecalho = {"alg": ALGORITMO_JWT, "typ": "JWT"}
    sem_assinatura = f"{_json_b64(cabecalho)}.{_json_b64(conteudo)}"
    return f"{sem_assinatura}.{_assinar(sem_assinatura)}"


def ler_token_acesso(token: str) -> dict[str, Any] | None:
    """Devolve o conteúdo do token, ou None se ele for inválido ou estiver expirado."""
    try:
        cabecalho_b64, conteudo_b64, assinatura = token.split(".", 2)
        sem_assinatura = f"{cabecalho_b64}.{conteudo_b64}"
        if not hmac.compare_digest(_assinar(sem_assinatura), assinatura):
            return None
        if _json_b64_ler(cabecalho_b64).get("alg") != ALGORITMO_JWT:
            return None
        conteudo = _json_b64_ler(conteudo_b64)
        if int(conteudo.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return conteudo
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def verificar_segredo_jwt() -> None:
    """Impede a API de ligar sem um segredo próprio.

    Antes havia um segredo padrão escrito no código. Como o código é público, quem lesse
    o repositório conseguiria fabricar um token de operador se o servidor fosse publicado
    sem configurar o segredo. Agora a API simplesmente não sobe nessa situação.
    """
    segredo = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(segredo) < TAMANHO_MINIMO_SEGREDO:
        raise RuntimeError(
            f"Configure JWT_SECRET_KEY com pelo menos {TAMANHO_MINIMO_SEGREDO} caracteres aleatórios. "
            'Para gerar um: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )


def _segredo_jwt() -> bytes:
    verificar_segredo_jwt()
    return os.getenv("JWT_SECRET_KEY", "").strip().encode("utf-8")


def _assinar(valor: str) -> str:
    return _b64(hmac.new(_segredo_jwt(), valor.encode("utf-8"), hashlib.sha256).digest())


def _json_b64(valor: dict[str, Any]) -> str:
    return _b64(json.dumps(valor, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _json_b64_ler(valor: str) -> dict[str, Any]:
    return json.loads(_b64_ler(valor).decode("utf-8"))


def _b64(valor: bytes) -> str:
    return base64.urlsafe_b64encode(valor).rstrip(b"=").decode("ascii")


def _b64_ler(valor: str) -> bytes:
    complemento = "=" * (-len(valor) % 4)
    return base64.urlsafe_b64decode(f"{valor}{complemento}")
