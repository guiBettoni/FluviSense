"""Os erros da API saem em português."""


def test_campo_obrigatorio_em_portugues(cliente, acesso):
    resposta = cliente.post("/api/rios", json={}, headers=acesso)
    assert resposta.status_code == 422
    assert resposta.json()["detalhe"] == [{"campo": "nome", "mensagem": "Nome: Campo obrigatório."}]


def test_texto_curto_demais_em_portugues(cliente, acesso):
    resposta = cliente.post("/api/rios", json={"nome": "A"}, headers=acesso)
    assert resposta.status_code == 422
    assert resposta.json()["detalhe"][0]["mensagem"] == "Nome: Texto curto demais (mínimo de 2 caracteres)."


def test_numero_invalido_em_portugues(cliente, acesso, criar_ponto):
    ponto = criar_ponto()
    resposta = cliente.post(f"/api/pontos/{ponto['id']}/medicoes", json={"distancia_cm": "abc"}, headers=acesso)
    assert resposta.status_code == 422
    assert resposta.json()["detalhe"][0]["mensagem"] == "Distância: Informe um número válido."


def test_rota_inexistente_em_portugues(cliente):
    resposta = cliente.get("/api/rota-que-nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["detalhe"] == "Recurso não encontrado."


def test_mensagem_das_regras_do_projeto_continua_igual(cliente, acesso, criar_ponto):
    # Regras escritas pelo projeto (aqui, a ordem dos critérios) já estavam em português.
    resposta = cliente.post(
        "/api/pontos",
        json={"codigo": "PT-M", "nome": "Ponto M", "distancia_atencao_cm": 50, "distancia_alerta_cm": 80, "distancia_critica_cm": 20},
        headers=acesso,
    )
    assert resposta.status_code == 422
    assert all("Value error" not in erro["mensagem"] for erro in resposta.json()["detalhe"])
