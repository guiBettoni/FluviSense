from conftest import dados_ponto


def test_dispositivo_precisa_da_chave_do_proprio_ponto(cliente, acesso, rio, criar_ponto):
    a = criar_ponto("PT-A")
    criar_ponto("PT-B")
    chave_a = cliente.post(f"/api/pontos/{a['id']}/chave-sensor", headers=acesso).json()["chave_sensor"]

    corpo = {"codigo_ponto": "PT-A", "distancia_cm": 250}
    assert cliente.post("/api/sensor/medicoes", json=corpo).status_code == 401
    assert cliente.post("/api/sensor/medicoes", json=corpo, headers={"X-Chave-Sensor": "errada"}).status_code == 401
    outro = {"codigo_ponto": "PT-B", "distancia_cm": 250}
    assert cliente.post("/api/sensor/medicoes", json=outro, headers={"X-Chave-Sensor": chave_a}).status_code == 401

    ok = cliente.post("/api/sensor/medicoes", json=corpo, headers={"X-Chave-Sensor": chave_a})
    assert ok.status_code == 201
    assert ok.json()["origem"] == "sensor"
    assert cliente.get("/api/publico/pontos").json()[0]["estado"]["distancia_cm"] == 250


def test_trocar_chave_invalida_a_anterior(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-K")
    primeira = cliente.post(f"/api/pontos/{ponto['id']}/chave-sensor", headers=acesso).json()["chave_sensor"]
    segunda = cliente.post(f"/api/pontos/{ponto['id']}/chave-sensor", headers=acesso).json()["chave_sensor"]
    corpo = {"codigo_ponto": "PT-K", "distancia_cm": 200}
    assert cliente.post("/api/sensor/medicoes", json=corpo, headers={"X-Chave-Sensor": primeira}).status_code == 401
    assert cliente.post("/api/sensor/medicoes", json=corpo, headers={"X-Chave-Sensor": segunda}).status_code == 201


def test_auditoria_registra_alteracoes_sem_guardar_segredos(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-AU")
    chave = cliente.post(f"/api/pontos/{ponto['id']}/chave-sensor", headers=acesso).json()["chave_sensor"]
    cliente.post(f"/api/pontos/{ponto['id']}/medicoes", json={"distancia_cm": 210, "origem": "manual"}, headers=acesso)
    cliente.post(f"/api/pontos/{ponto['id']}/simulacoes", json={"cenario": "subida", "distancia_inicial_cm": 300, "variacao_cm": 50, "quantidade": 3}, headers=acesso)
    eventos = cliente.get("/api/auditoria", headers=acesso).json()
    acoes = {e["acao"] for e in eventos}
    assert {"LOGIN_OPERADOR", "RIO_CRIADO", "PONTO_CRIADO", "CHAVE_DISPOSITIVO_GERADA", "MEDICAO_MANUAL_REGISTRADA", "SIMULACAO_GERADA"} <= acoes
    texto = str(eventos)
    assert chave not in texto
    assert "senha" not in texto and "senha-de-teste" not in texto
