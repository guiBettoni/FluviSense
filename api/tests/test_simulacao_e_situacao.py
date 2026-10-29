from datetime import datetime, timedelta, timezone

from conftest import enviar


def simular(cliente, acesso, pid, **corpo):
    resposta = cliente.post(f"/api/pontos/{pid}/simulacoes", json=corpo, headers=acesso)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_subida_reduz_a_distancia_e_eleva_a_classificacao(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    resultado = simular(cliente, acesso, pid, cenario="subida", distancia_inicial_cm=260, variacao_cm=180, quantidade=10, intervalo_minutos=5)
    distancias = [m["distancia_cm"] for m in resultado["medicoes"]]
    assert distancias[0] == 260 and distancias[-1] == 80
    assert distancias == sorted(distancias, reverse=True)
    assert all(m["origem"] == "simulada" for m in resultado["medicoes"])
    horarios = [m["medida_em"] for m in resultado["medicoes"]]
    assert horarios == sorted(horarios)
    simulado = cliente.get(f"/api/pontos/{pid}", headers=acesso).json()["estado_simulado"]
    assert simulado["situacao"] == "vermelho"
    assert resultado["suspeitas"] == 0


def test_descida_aumenta_a_distancia(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    resultado = simular(cliente, acesso, pid, cenario="descida", distancia_inicial_cm=90, variacao_cm=200, quantidade=8, intervalo_minutos=10)
    distancias = [m["distancia_cm"] for m in resultado["medicoes"]]
    assert distancias == sorted(distancias)
    assert distancias[-1] == 290
    assert cliente.get(f"/api/pontos/{pid}", headers=acesso).json()["estado_simulado"]["situacao"] == "verde"


def test_oscilacao_fica_em_torno_do_valor_inicial(cliente, acesso, ponto_com_criterios):
    resultado = simular(cliente, acesso, ponto_com_criterios["id"], cenario="oscilacao", distancia_inicial_cm=250, variacao_cm=40, quantidade=13, intervalo_minutos=5)
    distancias = [m["distancia_cm"] for m in resultado["medicoes"]]
    assert max(distancias) == 270 and min(distancias) == 230
    assert distancias[0] == distancias[-1] == 250


def test_simulacao_que_zeraria_a_distancia_e_rejeitada(cliente, acesso, ponto_com_criterios):
    resposta = cliente.post(
        f"/api/pontos/{ponto_com_criterios['id']}/simulacoes",
        json={"cenario": "subida", "distancia_inicial_cm": 100, "variacao_cm": 100},
        headers=acesso,
    )
    assert resposta.status_code == 422


def test_simulacao_nao_contamina_dados_reais_nem_o_mapa(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    enviar(cliente, acesso, pid, 280)  # real
    simular(cliente, acesso, pid, cenario="subida", distancia_inicial_cm=280, variacao_cm=200, quantidade=6, intervalo_minutos=1)
    ponto = cliente.get(f"/api/pontos/{pid}", headers=acesso).json()
    assert ponto["estado_real"]["situacao"] == "verde" and ponto["estado_real"]["distancia_cm"] == 280
    assert ponto["estado_simulado"]["situacao"] == "vermelho"
    publico = cliente.get("/api/publico/pontos").json()[0]["estado"]
    assert publico["situacao"] == "verde" and publico["distancia_cm"] == 280
    # a próxima medição real usa como referência só dados reais
    assert enviar(cliente, acesso, pid, 281)["referencia_cm"] is None


def test_limpar_simulacao_apaga_so_simuladas(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    enviar(cliente, acesso, pid, 280)
    simular(cliente, acesso, pid, cenario="oscilacao", distancia_inicial_cm=250, variacao_cm=20, quantidade=5, intervalo_minutos=1)
    apagadas = cliente.delete(f"/api/pontos/{pid}/medicoes/simuladas", headers=acesso).json()
    assert apagadas == {"apagadas": 5}
    restantes = cliente.get(f"/api/pontos/{pid}/medicoes?modo=todas", headers=acesso).json()
    assert [m["origem"] for m in restantes] == ["manual"]


def test_dado_antigo_aparece_como_desatualizado(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-OLD", distancia_atencao_cm=200, distancia_alerta_cm=150, distancia_critica_cm=100, minutos_para_desatualizar=60)
    antigo = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    enviar(cliente, acesso, ponto["id"], 90, "manual", antigo)
    publico = cliente.get("/api/publico/pontos").json()[0]["estado"]
    assert publico["desatualizado"] is True
    assert publico["situacao"] == "desatualizado"
    assert publico["classificacao"] == "vermelho"  # mantida só como informação do último registro


def test_ponto_sem_medicao(cliente, acesso, ponto_com_criterios):
    publico = cliente.get("/api/publico/pontos").json()[0]["estado"]
    assert publico["situacao"] == "sem_dados"


def test_ocorrencia_manual_prevalece_e_ao_encerrar_volta_ao_calculo(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    enviar(cliente, acesso, pid, 280)
    aberta = cliente.post(f"/api/pontos/{pid}/ocorrencias", json={"classificacao": "laranja", "motivo": "Água na pista vista pela equipe"}, headers=acesso)
    assert aberta.status_code == 201
    segunda = cliente.post(f"/api/pontos/{pid}/ocorrencias", json={"motivo": "outra"}, headers=acesso)
    assert segunda.status_code == 409
    publico = cliente.get("/api/publico/pontos").json()[0]["estado"]
    assert publico["situacao"] == "laranja"
    assert publico["ocorrencia"]["motivo"] == "Água na pista vista pela equipe"
    assert len(cliente.get("/api/ocorrencias", headers=acesso).json()) == 1
    encerrada = cliente.put(f"/api/ocorrencias/{aberta.json()['id']}/encerrar", headers=acesso)
    assert encerrada.status_code == 200
    assert cliente.put(f"/api/ocorrencias/{aberta.json()['id']}/encerrar", headers=acesso).status_code == 409
    assert cliente.get("/api/publico/pontos").json()[0]["estado"]["situacao"] == "verde"
    assert cliente.get("/api/ocorrencias", headers=acesso).json() == []
    assert len(cliente.get("/api/ocorrencias?situacao=todas", headers=acesso).json()) == 1
