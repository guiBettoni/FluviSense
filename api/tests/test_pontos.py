import json

from conftest import dados_ponto


def test_varios_pontos_com_configuracao_propria(cliente, acesso, criar_ponto):
    a = criar_ponto("PT-A", distancia_atencao_cm=300, distancia_alerta_cm=250, distancia_critica_cm=200, minutos_para_desatualizar=30)
    b = criar_ponto("pt-b", salto_maximo_cm=40)
    assert b["codigo"] == "PT-B"
    pontos = {p["codigo"]: p for p in cliente.get("/api/pontos", headers=acesso).json()}
    assert pontos["PT-A"]["distancia_critica_cm"] == 200
    assert pontos["PT-A"]["minutos_para_desatualizar"] == 30
    assert pontos["PT-B"]["distancia_atencao_cm"] is None
    assert pontos["PT-B"]["salto_maximo_cm"] == 40
    assert pontos["PT-A"]["criterios_provisorios"] is True
    assert a["rio_nome"] == "Rio Cubatão do Sul"


def test_codigo_duplicado_e_rio_inexistente(cliente, acesso, rio, criar_ponto):
    criar_ponto("PT-01")
    repetido = cliente.post("/api/pontos", json=dados_ponto(rio["id"], "pt-01"), headers=acesso)
    assert repetido.status_code == 409
    sem_rio = cliente.post("/api/pontos", json=dados_ponto(9999, "PT-02"), headers=acesso)
    assert sem_rio.status_code == 400


def test_criterios_precisam_ser_completos_e_ordenados(cliente, acesso, rio, criar_ponto):
    parcial = cliente.post("/api/pontos", json=dados_ponto(rio["id"], "X1", distancia_atencao_cm=100), headers=acesso)
    assert parcial.status_code == 422
    ordem_errada = cliente.post(
        "/api/pontos",
        json=dados_ponto(rio["id"], "X2", distancia_atencao_cm=100, distancia_alerta_cm=150, distancia_critica_cm=50),
        headers=acesso,
    )
    assert ordem_errada.status_code == 422
    ponto = criar_ponto("X3", distancia_atencao_cm=200, distancia_alerta_cm=150, distancia_critica_cm=100)
    alteracao_invalida = cliente.put(f"/api/pontos/{ponto['id']}", json={"distancia_critica_cm": 180}, headers=acesso)
    assert alteracao_invalida.status_code == 400
    limpo = cliente.put(
        f"/api/pontos/{ponto['id']}",
        json={"distancia_atencao_cm": None, "distancia_alerta_cm": None, "distancia_critica_cm": None},
        headers=acesso,
    )
    assert limpo.status_code == 200
    assert limpo.json()["distancia_atencao_cm"] is None


def test_alteracao_de_criterios_fica_na_auditoria_com_antes_e_depois(cliente, acesso, ponto_com_criterios):
    ponto_id = ponto_com_criterios["id"]
    resposta = cliente.put(f"/api/pontos/{ponto_id}", json={"distancia_atencao_cm": 220, "justificativa_criterios": "Revisado em campo"}, headers=acesso)
    assert resposta.status_code == 200
    evento = next(e for e in cliente.get("/api/auditoria", headers=acesso).json() if e["acao"] == "CRITERIOS_ALTERADOS")
    detalhes = json.loads(evento["detalhes"])
    assert detalhes["distancia_atencao_cm"] == {"antes": 200.0, "depois": 220.0}
    assert evento["autor"] == "operador@teste.local"


def test_desativar_ponto_mantem_historico_e_tira_do_mapa(cliente, acesso, criar_ponto):
    from conftest import enviar

    ponto = criar_ponto("PT-D")
    enviar(cliente, acesso, ponto["id"], 250)
    assert cliente.delete(f"/api/pontos/{ponto['id']}", headers=acesso).status_code == 204
    assert all(p["codigo"] != "PT-D" for p in cliente.get("/api/publico/pontos").json())
    historico = cliente.get(f"/api/pontos/{ponto['id']}/medicoes", headers=acesso).json()
    assert len(historico) == 1
    bloqueado = cliente.post(f"/api/pontos/{ponto['id']}/medicoes", json={"distancia_cm": 240}, headers=acesso)
    assert bloqueado.status_code == 400


def test_rios(cliente, acesso, rio):
    assert cliente.post("/api/rios", json={"nome": "rio cubatão do sul"}, headers=acesso).status_code == 409
    segunda = cliente.post("/api/rios", json={"nome": "Rio Aririú"}, headers=acesso)
    assert segunda.status_code == 201
    renomeado = cliente.put(f"/api/rios/{segunda.json()['id']}", json={"nome": "Rio Aririu"}, headers=acesso)
    assert renomeado.json()["nome"] == "Rio Aririu"
    nomes = [r["nome"] for r in cliente.get("/api/rios").json()]
    assert nomes == ["Rio Aririu", "Rio Cubatão do Sul"]


def test_rota_publica_nao_expoe_configuracao_interna(cliente, acesso, ponto_com_criterios):
    cliente.post(f"/api/pontos/{ponto_com_criterios['id']}/chave-sensor", headers=acesso)
    publico = cliente.get("/api/publico/pontos").json()[0]
    assert "hash_chave_sensor" not in publico and "possui_chave_sensor" not in publico
    assert "salto_maximo_cm" not in publico
    assert set(publico["estado"]) >= {"situacao", "desatualizado", "validade"}
