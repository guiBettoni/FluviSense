"""Exclusão de rios e pontos: só quando não há dados que dependam deles."""

from conftest import dados_ponto, enviar


def test_excluir_rio_sem_pontos(cliente, acesso):
    rio = cliente.post("/api/rios", json={"nome": "Rio Temporário"}, headers=acesso).json()
    assert cliente.delete(f"/api/rios/{rio['id']}", headers=acesso).status_code == 204
    assert all(r["nome"] != "Rio Temporário" for r in cliente.get("/api/rios").json())
    assert cliente.delete(f"/api/rios/{rio['id']}", headers=acesso).status_code == 404
    eventos = cliente.get("/api/auditoria", headers=acesso).json()
    assert any(e["acao"] == "RIO_EXCLUIDO" and "Rio Temporário" in e["detalhes"] for e in eventos)


def test_rio_com_pontos_nao_pode_ser_excluido(cliente, acesso, rio, criar_ponto):
    ponto = criar_ponto("PT-R")
    cliente.delete(f"/api/pontos/{ponto['id']}", headers=acesso)  # ponto desativado continua ligado ao rio
    resposta = cliente.delete(f"/api/rios/{rio['id']}", headers=acesso)
    assert resposta.status_code == 409
    assert "1 ponto ligado" in resposta.json()["detalhe"]
    assert any(r["id"] == rio["id"] for r in cliente.get("/api/rios").json())


def test_rio_liberado_depois_de_mover_o_ponto(cliente, acesso, rio, criar_ponto):
    ponto = criar_ponto("PT-M")
    outro = cliente.post("/api/rios", json={"nome": "Rio Destino"}, headers=acesso).json()
    assert cliente.put(f"/api/pontos/{ponto['id']}", json={"rio_id": outro["id"]}, headers=acesso).status_code == 200
    assert cliente.delete(f"/api/rios/{rio['id']}", headers=acesso).status_code == 204


def test_excluir_ponto_sem_historico_real_apaga_tambem_as_simuladas(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-X")
    cliente.post(f"/api/pontos/{ponto['id']}/simulacoes", json={"cenario": "subida", "distancia_inicial_cm": 300, "variacao_cm": 50, "quantidade": 4}, headers=acesso)
    assert cliente.delete(f"/api/pontos/{ponto['id']}/definitivo", headers=acesso).status_code == 204
    assert cliente.get(f"/api/pontos/{ponto['id']}", headers=acesso).status_code == 404
    assert all(p["codigo"] != "PT-X" for p in cliente.get("/api/pontos", headers=acesso).json())
    # o código fica livre para um novo cadastro
    assert cliente.post("/api/pontos", json=dados_ponto(ponto["rio_id"], "PT-X"), headers=acesso).status_code == 201
    evento = next(e for e in cliente.get("/api/auditoria", headers=acesso).json() if e["acao"] == "PONTO_EXCLUIDO")
    assert '"medicoes_simuladas_apagadas": 4' in evento["detalhes"]


def test_ponto_com_medicao_real_nao_pode_ser_excluido(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-H")
    enviar(cliente, acesso, ponto["id"], 250)
    resposta = cliente.delete(f"/api/pontos/{ponto['id']}/definitivo", headers=acesso)
    assert resposta.status_code == 409
    assert "Desativar" in resposta.json()["detalhe"]
    historico = cliente.get(f"/api/pontos/{ponto['id']}/medicoes", headers=acesso).json()
    assert len(historico) == 1


def test_ponto_com_ocorrencia_nao_pode_ser_excluido(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-O")
    cliente.post(f"/api/pontos/{ponto['id']}/ocorrencias", json={"motivo": "Água na pista"}, headers=acesso)
    resposta = cliente.delete(f"/api/pontos/{ponto['id']}/definitivo", headers=acesso)
    assert resposta.status_code == 409
    assert "ocorrência" in resposta.json()["detalhe"]


def test_exclusao_exige_operador_e_ponto_existente(cliente, acesso):
    assert cliente.delete("/api/pontos/1/definitivo").status_code == 401
    assert cliente.delete("/api/rios/1").status_code == 401
    assert cliente.delete("/api/pontos/999/definitivo", headers=acesso).status_code == 404
