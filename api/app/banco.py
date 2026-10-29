"""Conexão com o banco de dados."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PASTA_API = Path(__file__).resolve().parents[1]
load_dotenv(PASTA_API / ".env")


def url_do_banco() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL não configurada. Copie api/.env.example para api/.env e preencha a conexão PostgreSQL."
        )
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Base(DeclarativeBase):
    pass


def _opcoes_do_motor(url: str) -> dict:
    # SQLite só é usado nos testes automáticos; ele não aceita as opções de conexão do PostgreSQL.
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {
        "pool_pre_ping": True,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }


_url = url_do_banco()
motor = create_engine(_url, **_opcoes_do_motor(_url))

SessaoLocal = sessionmaker(bind=motor, autoflush=False, autocommit=False, expire_on_commit=False)


def obter_sessao() -> Generator[Session, None, None]:
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
