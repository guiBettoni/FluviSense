"""Ponto de entrada da API. Para ligar: uvicorn app.main:app --port 8001"""

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.mensagens import erro_de_validacao, erro_http
from app.rotas import roteador
from app.seguranca import verificar_segredo_jwt


def _origens_permitidas() -> list[str]:
    origens = [origem.strip() for origem in os.getenv("CORS_ORIGINS", "*").split(",") if origem.strip()]
    return origens or ["*"]


# Nomes das variáveis de ambiente no padrão usado pelo FastAPI e pelo Render.
ambiente = os.getenv("APP_ENV", "development").strip().lower()
origens_permitidas = _origens_permitidas()
if ambiente in {"production", "prod"} and "*" in origens_permitidas:
    raise RuntimeError("Em produção, configure CORS_ORIGINS com o endereço público do site.")
verificar_segredo_jwt()  # vale para qualquer ambiente: sem segredo, a API não liga


app = FastAPI(
    title="API do FluviSense",
    description="Monitoramento da distância entre sensores e a superfície de rios em Palhoça/SC.",
    version="2.1.0",
)

# CORS: diz ao navegador quais sites podem chamar esta API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
def conflito_no_banco(requisicao: Request, erro: IntegrityError):
    # Conflitos que escaparam das validações (ex.: duas requisições simultâneas com o mesmo código).
    return JSONResponse(status_code=409, content={"detalhe": "Operação conflita com dados já existentes."})


# Erros de validação e erros HTTP padrão saem em português.
app.add_exception_handler(RequestValidationError, erro_de_validacao)
app.add_exception_handler(StarletteHTTPException, erro_http)

app.include_router(roteador)
