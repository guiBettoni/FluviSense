from datetime import datetime, timedelta, timezone

from conftest import enviar


def test_medicao_guarda_valor_unidade_horario_ponto_e_origem(cliente, acesso, ponto_com_criterios):
    quando = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    m = enviar(cliente, acesso, ponto_com_criterios["id"], 245.5, "manual", quando)
    assert m["distancia_cm"] == 245.5
    assert m["unidade"] == "cm"
    assert m["origem"] == "manual"
    assert m["ponto_id"] == ponto_com_criterios["id"]
    assert m["validade"] == "valida"
    assert m["registrada_por"] == "operador@teste.local"
    assert datetime.fromisoformat(m["medida_em"]) == datetime.fromisoformat(quando)


def test_historico_ordenado_e_filtrado_por_modo(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    agora = datetime.now(timezone.utc)
    for minutos, distancia in [(30, 260), (20, 255), (10, 250)]:
        enviar(cliente, acesso, pid, distancia, "manual", (agora - timedelta(minutes=minutos)).isoformat())
    enviar(cliente, acesso, pid, 120, "simulada")
    reais = cliente.get(f"/api/pontos/{pid}/medicoes?modo=real", headers=acesso).json()
    assert [m["distancia_cm"] for m in reais] == [250, 255, 260]
    simulado = cliente.get(f"/api/pontos/{pid}/medicoes?modo=simulada", headers=acesso).json()
    assert [m["origem"] for m in simulado] == ["simulada"]
    assert len(cliente.get(f"/api/pontos/{pid}/medicoes?modo=todas", headers=acesso).json()) == 4
    desde = (agora - timedelta(minutes=15)).isoformat()
    janela = cliente.get(f"/api/pontos/{pid}/medicoes", params={"desde": desde}, headers=acesso).json()
    assert [m["distancia_cm"] for m in janela] == [250]


def test_horario_no_futuro_e_rejeitado(cliente, acesso, ponto_com_criterios):
    futuro = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    resposta = cliente.post(f"/api/pontos/{ponto_com_criterios['id']}/medicoes", json={"distancia_cm": 200, "medida_em": futuro}, headers=acesso)
    assert resposta.status_code == 422


def test_medicao_invalida_e_guardada_mas_nao_muda_a_situacao(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-INV", distancia_minima_valida_cm=20, distancia_maxima_valida_cm=500)
    pid = ponto["id"]
    enviar(cliente, acesso, pid, 300)
    for valor in (0, -5, 10, 800):
        m = enviar(cliente, acesso, pid, valor)
        assert m["validade"] == "invalida"
        assert m["motivo_validade"]
        assert m["classificacao"] is None
    estado = cliente.get(f"/api/pontos/{pid}", headers=acesso).json()["estado_real"]
    assert estado["distancia_cm"] == 300
    assert estado["ultima_recebida_invalida"] is True
    assert len(cliente.get(f"/api/pontos/{pid}/medicoes", headers=acesso).json()) == 5


def test_salto_brusco_e_suspeito_mas_preservado_e_exibido(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    for valor in (300, 302, 299):
        assert enviar(cliente, acesso, pid, valor)["validade"] == "valida"
    salto = enviar(cliente, acesso, pid, 90)  # água subiu muito de uma vez
    assert salto["validade"] == "suspeita"
    assert salto["referencia_cm"] == 300
    assert "Variação" in salto["motivo_validade"]
    assert salto["classificacao"] == "vermelho"
    estado = cliente.get(f"/api/pontos/{pid}", headers=acesso).json()["estado_real"]
    assert estado["distancia_cm"] == 90
    assert estado["validade"] == "suspeita"
    assert estado["situacao"] == "vermelho"


def test_mudanca_que_se_mantem_vira_referencia_sem_travar(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    for valor in (300, 300, 300):
        enviar(cliente, acesso, pid, valor)
    resultados = [enviar(cliente, acesso, pid, valor)["validade"] for valor in (90, 90, 90, 92)]
    assert resultados == ["suspeita", "suspeita", "valida", "valida"]


def test_pico_isolado_nao_contamina_a_referencia(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    for valor in (300, 300, 300):
        enviar(cliente, acesso, pid, valor)
    assert enviar(cliente, acesso, pid, 50)["validade"] == "suspeita"
    depois = enviar(cliente, acesso, pid, 301)
    assert depois["validade"] == "valida"
    assert depois["referencia_cm"] == 300


def test_limite_de_salto_configurado_no_ponto(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-J", salto_maximo_cm=10)
    pid = ponto["id"]
    for valor in (300, 300, 300):
        enviar(cliente, acesso, pid, valor)
    assert enviar(cliente, acesso, pid, 309)["validade"] == "valida"
    assert enviar(cliente, acesso, pid, 285)["validade"] == "suspeita"


def test_classificacao_por_distancia(cliente, acesso, ponto_com_criterios):
    pid = ponto_com_criterios["id"]
    esperado = {250: "verde", 200: "amarelo", 150: "laranja", 100: "vermelho", 40: "vermelho"}
    for distancia, classificacao in esperado.items():
        cliente.delete(f"/api/pontos/{pid}/medicoes/simuladas", headers=acesso)
        m = enviar(cliente, acesso, pid, distancia, "simulada")
        assert m["classificacao"] == classificacao, distancia


def test_ponto_sem_criterio(cliente, acesso, criar_ponto):
    ponto = criar_ponto("PT-SC")
    enviar(cliente, acesso, ponto["id"], 120)
    estado = cliente.get(f"/api/pontos/{ponto['id']}", headers=acesso).json()["estado_real"]
    assert estado["situacao"] == "sem_criterio"
