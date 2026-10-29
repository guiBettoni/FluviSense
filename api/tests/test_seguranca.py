import pytest
from sqlalchemy import text

from app.banco import motor
from app.seguranca import verificar_segredo_jwt
from conftest import EMAIL_OPERADOR, SENHA_OPERADOR, USANDO_POSTGRES


def entrar(cliente, senha):
    return cliente.post("/api/autenticacao/login", json={"email": EMAIL_OPERADOR, "senha": senha})


def test_login_bloqueia_depois_de_5_senhas_erradas(cliente):
    for _ in range(5):
        assert entrar(cliente, "errada").status_code == 401
    bloqueado = entrar(cliente, SENHA_OPERADOR)  # nem a senha certa entra durante o bloqueio
    assert bloqueado.status_code == 429
    assert "Tente de novo em 15 minutos" in bloqueado.json()["detalhe"]
    assert bloqueado.headers["Retry-After"]


def test_bloqueio_termina_depois_do_tempo(cliente, monkeypatch):
    from app.servicos import limite_login

    relogio = [1000.0]
    monkeypatch.setattr(limite_login, "_agora", lambda: relogio[0])
    for _ in range(5):
        entrar(cliente, "errada")
    assert entrar(cliente, SENHA_OPERADOR).status_code == 429
    relogio[0] += limite_login.TEMPO_BLOQUEIO + 1
    assert entrar(cliente, SENHA_OPERADOR).status_code == 200


def test_login_certo_zera_a_contagem(cliente):
    for _ in range(4):
        entrar(cliente, "errada")
    assert entrar(cliente, SENHA_OPERADOR).status_code == 200
    for _ in range(4):
        assert entrar(cliente, "errada").status_code == 401  # contagem recomeçou do zero


@pytest.mark.parametrize("segredo", ["", "curto-demais"])
def test_api_nao_liga_sem_segredo_forte(monkeypatch, segredo):
    monkeypatch.setenv("JWT_SECRET_KEY", segredo)
    with pytest.raises(RuntimeError):
        verificar_segredo_jwt()


@pytest.mark.skipif(not USANDO_POSTGRES, reason="RLS só existe no PostgreSQL.")
def test_rls_ligada_em_todas_as_tabelas():
    with motor.connect() as conexao:
        linhas = conexao.execute(text("select tablename, rowsecurity from pg_tables where schemaname = 'public'")).all()
    assert linhas
    assert [nome for nome, ligada in linhas if not ligada] == []
