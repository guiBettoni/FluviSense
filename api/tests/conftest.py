"""Configuração dos testes.

Por padrão os testes usam um SQLite temporário (tabelas criadas pelos modelos).
Para testar também as migrações reais, aponte TEST_DATABASE_URL para um PostgreSQL
VAZIO e descartável: o schema public é apagado e recriado pelas migrações.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest


PASTA_API = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA_API))

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()
USANDO_POSTGRES = TEST_DATABASE_URL.startswith("postgres")
if USANDO_POSTGRES:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
else:
    _arquivo = Path(tempfile.mkdtemp()) / "fluvisense_teste.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{_arquivo}"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "segredo-usado-apenas-nos-testes-automaticos-0123456789"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.banco import Base, SessaoLocal, motor  # noqa: E402
from app.modelos import Usuario  # noqa: E402
from app.main import app  # noqa: E402
from app.seguranca import gerar_hash_senha  # noqa: E402


TABELAS = ["eventos_auditoria", "medicoes", "ocorrencias", "pontos_monitoramento", "rios", "usuarios"]
EMAIL_OPERADOR = "operador@teste.local"
SENHA_OPERADOR = "senha-de-teste-123"


def _preparar_banco() -> None:
    if USANDO_POSTGRES:
        with motor.begin() as conexao:
            conexao.execute(text("drop schema public cascade; create schema public;"))
        import runpy
        argv = sys.argv
        sys.argv = ["migrar.py"]
        try:
            runpy.run_path(str(PASTA_API / "scripts" / "migrar.py"), run_name="__main__")
        finally:
            sys.argv = argv
    else:
        Base.metadata.create_all(motor)


_preparar_banco()


@pytest.fixture(autouse=True)
def limpar_tabelas():
    from app.servicos import limite_login

    limite_login.limpar()
    with motor.begin() as conexao:
        if USANDO_POSTGRES:
            conexao.execute(text(f"truncate {', '.join(TABELAS)} restart identity cascade"))
        else:
            for tabela in TABELAS:
                conexao.execute(text(f"delete from {tabela}"))
    with SessaoLocal() as sessao:
        sessao.add(Usuario(nome="Operador Teste", email=EMAIL_OPERADOR, hash_senha=gerar_hash_senha(SENHA_OPERADOR)))
        sessao.commit()
    yield


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def acesso(cliente):
    """Cabeçalho com o token do operador, para as rotas protegidas."""
    resposta = cliente.post("/api/autenticacao/login", json={"email": EMAIL_OPERADOR, "senha": SENHA_OPERADOR})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['token_acesso']}"}


@pytest.fixture
def rio(cliente, acesso):
    resposta = cliente.post("/api/rios", json={"nome": "Rio Cubatão do Sul"}, headers=acesso)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def dados_ponto(rio_id: int, codigo: str = "PT-01", **extras) -> dict:
    dados = {
        "codigo": codigo,
        "nome": f"Ponto {codigo}",
        "rio_id": rio_id,
        "bairro": "Centro",
        "latitude": -27.645,
        "longitude": -48.67,
    }
    dados.update(extras)
    return dados


@pytest.fixture
def criar_ponto(cliente, acesso, rio):
    def _criar(codigo: str = "PT-01", **extras) -> dict:
        resposta = cliente.post("/api/pontos", json=dados_ponto(rio["id"], codigo, **extras), headers=acesso)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def ponto_com_criterios(criar_ponto):
    # Valores só para teste. Não são limiares hidrológicos de nenhum rio real.
    return criar_ponto(distancia_atencao_cm=200, distancia_alerta_cm=150, distancia_critica_cm=100)


def enviar(cliente, acesso, ponto_id: int, distancia: float, origem: str = "manual", medida_em: str | None = None):
    corpo = {"distancia_cm": distancia, "origem": origem}
    if medida_em:
        corpo["medida_em"] = medida_em
    resposta = cliente.post(f"/api/pontos/{ponto_id}/medicoes", json=corpo, headers=acesso)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()
