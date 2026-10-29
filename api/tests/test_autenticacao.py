import pytest

from app.seguranca import criar_token_acesso


def test_login_correto_e_incorreto(cliente):
    ok = cliente.post("/api/autenticacao/login", json={"email": "OPERADOR@teste.local", "senha": "senha-de-teste-123"})
    assert ok.status_code == 200
    assert ok.json()["usuario"]["perfil"] == "OPERADOR"
    errado = cliente.post("/api/autenticacao/login", json={"email": "operador@teste.local", "senha": "errada"})
    assert errado.status_code == 401


ROTAS_DO_OPERADOR = [
    ("get", "/api/pontos"),
    ("post", "/api/pontos"),
    ("put", "/api/pontos/1"),
    ("delete", "/api/pontos/1"),
    ("delete", "/api/pontos/1/definitivo"),
    ("delete", "/api/rios/1"),
    ("post", "/api/pontos/1/chave-sensor"),
    ("get", "/api/pontos/1/medicoes"),
    ("post", "/api/pontos/1/medicoes"),
    ("post", "/api/pontos/1/simulacoes"),
    ("delete", "/api/pontos/1/medicoes/simuladas"),
    ("post", "/api/rios"),
    ("put", "/api/rios/1"),
    ("get", "/api/ocorrencias"),
    ("post", "/api/pontos/1/ocorrencias"),
    ("put", "/api/ocorrencias/1/encerrar"),
    ("get", "/api/auditoria"),
]


@pytest.mark.parametrize("metodo,caminho", ROTAS_DO_OPERADOR)
def test_operacoes_administrativas_exigem_token(cliente, metodo, caminho):
    resposta = getattr(cliente, metodo)(caminho)
    assert resposta.status_code == 401


def test_token_invalido_ou_de_outro_papel(cliente):
    assert cliente.get("/api/pontos", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
    outro_perfil = criar_token_acesso("1", "MORADOR")
    assert cliente.get("/api/pontos", headers={"Authorization": f"Bearer {outro_perfil}"}).status_code == 403


def test_rotas_publicas_nao_exigem_token(cliente):
    assert cliente.get("/api/saude").status_code == 200
    assert cliente.get("/api/publico/pontos").status_code == 200
    assert cliente.get("/api/rios").status_code == 200
