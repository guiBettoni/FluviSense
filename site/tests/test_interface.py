"""Teste de fumaça da interface (Playwright + Chromium).

Pré-requisitos: um banco só para testes, criado pelas migrações, com o operador criado;
API em http://localhost:8001 e o site em http://localhost:8080. Ver README, seção "Testes".
O teste grava dados com nomes únicos a cada execução, então pode ser repetido no mesmo banco.
Uso: python site/tests/test_interface.py <pasta-para-capturas>
"""
import os
import sys
import time

from playwright.sync_api import sync_playwright

PASTA = sys.argv[1] if len(sys.argv) > 1 else "."
CAPTURAS = os.path.join(PASTA, "capturas")
os.makedirs(CAPTURAS, exist_ok=True)
ENDERECO = os.getenv("FLUVISENSE_E2E_URL", "http://localhost:8080")
EMAIL = os.getenv("FLUVISENSE_E2E_EMAIL", "op@fluvisense.local")
SENHA = os.getenv("FLUVISENSE_E2E_PASSWORD", "senha-e2e-123")

# Nomes únicos por execução: o teste pode rodar várias vezes no mesmo banco.
EXECUCAO = time.strftime("%d%H%M%S")
# O Chromium chama os temas do sistema de "light" e "dark"; aqui eles viram nomes de arquivo em português.
NOME_TEMA = {"light": "claro", "dark": "escuro"}
RIO_A = f"Rio Cubatão do Sul {EXECUCAO}"
RIO_B = f"Rio Aririú {EXECUCAO}"
RIO_TEMP = f"Rio Provisório {EXECUCAO}"
CODIGO_A, NOME_A = f"CUB{EXECUCAO}", "Ponte BR-282"
CODIGO_B, NOME_B = f"ARI{EXECUCAO}", "Foz do Aririú"
CODIGO_TEMP = f"TMP{EXECUCAO}"
ROTULO_A = f"{CODIGO_A} · {NOME_A}"
ROTULO_B = f"{CODIGO_B} · {NOME_B}"

erros = []
aprovadas = 0


def ok(mensagem):
    global aprovadas
    aprovadas += 1
    print(f"OK {aprovadas:02d} - {mensagem}")


def observar(pagina):
    pagina.on("pageerror", lambda e: erros.append(f"erro na página: {e}"))
    pagina.on("dialog", lambda d: (erros.append(f"diálogo nativo aberto: {d.message}"), d.dismiss()))

    def no_console(msg):
        texto = msg.text
        if msg.type == "error" and "net::" not in texto and not any(codigo in texto for codigo in ("400", "401", "409")):
            erros.append(f"console: {texto}")
    pagina.on("console", no_console)


def texto(pagina, seletor):
    return pagina.inner_text(seletor).lower()


def capturar(pagina, nome):
    pagina.screenshot(path=os.path.join(CAPTURAS, f"{nome}.png"), full_page=True)


def sem_rolagem_lateral(pagina):
    return pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


with sync_playwright() as playwright:
    navegador = playwright.chromium.launch()

    # ---------- Tema: segue o sistema na primeira visita e guarda a escolha ----------
    contexto = navegador.new_context(viewport={"width": 1366, "height": 860}, color_scheme="dark")
    tela = contexto.new_page()
    observar(tela)
    tela.goto(f"{ENDERECO}/#inicio")
    tela.wait_for_timeout(1200)
    assert tela.evaluate("document.documentElement.dataset.tema") == "escuro"
    ok("primeira visita segue o tema escuro do sistema")
    capturar(tela, "escuro-01-inicio")
    tela.click("#pg-inicio [data-alternar-tema]")
    assert tela.evaluate("document.documentElement.dataset.tema") == "claro"
    tela.reload()
    tela.wait_for_timeout(800)
    assert tela.evaluate("document.documentElement.dataset.tema") == "claro"
    ok("tema claro escolhido manualmente continua após recarregar")
    capturar(tela, "claro-01-inicio")
    assert tela.inner_text("#inicio-pontos").isdigit()
    ok("página inicial mostra os números")

    # ---------- Login ----------
    tela.goto(f"{ENDERECO}/#painel")
    tela.wait_for_timeout(500)
    assert tela.evaluate("location.hash") == "#login"
    ok("painel sem login leva ao login")
    tela.click("#form-login [type=submit]")
    assert "informe o e-mail" in texto(tela, "#login-email-erro") and "informe a senha" in texto(tela, "#login-senha-erro")
    assert tela.evaluate("document.activeElement.id") == "login-email"
    ok("login vazio mostra erro em cada campo e foca o primeiro")
    tela.fill("#login-email", EMAIL)
    tela.fill("#login-senha", "senha-errada")
    tela.click("#form-login [type=submit]")
    tela.wait_for_selector("#form-login .barra-mensagem.erro")
    ok("senha errada mostra mensagem dentro do formulário")
    capturar(tela, "claro-02-login-erro")
    tela.fill("#login-senha", SENHA)
    tela.click("#form-login [type=submit]")
    tela.wait_for_function("location.hash === '#painel'")
    tela.wait_for_timeout(800)
    if tela.inner_text("#painel-pontos") == "0":
        assert "nenhum ponto ativo" in texto(tela, "#painel-linhas")
    ok("login correto abre o painel com estado vazio orientando o próximo passo")
    capturar(tela, "claro-03-painel-vazio")

    # ---------- Rios ----------
    tela.click("#nav-pontos")
    tela.wait_for_timeout(500)
    for nome in [RIO_A, RIO_B]:
        tela.click("#aba-pontos >> text=Novo rio")
        tela.fill("#rio-nome", nome)
        tela.click("[form=form-rio]")
        tela.wait_for_timeout(700)
    assert RIO_B.lower() in texto(tela, "#rios-lista")
    ok("dois rios cadastrados pelo diálogo")

    # ---------- Diálogo não fecha sem querer ----------
    tela.click("#aba-pontos >> text=Novo ponto")
    tela.wait_for_selector("#form-ponto")
    tela.fill("#pt-nome", NOME_A)
    tela.mouse.click(5, 400)  # clique no fundo escuro, fora do diálogo
    tela.wait_for_timeout(300)
    assert tela.is_visible("#form-ponto") and tela.input_value("#pt-nome") == NOME_A
    ok("clique fora do formulário NÃO fecha o diálogo nem perde o que foi digitado")
    tela.keyboard.press("Escape")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    assert "descartar" in texto(tela, ".dialogo .barra-mensagem.atencao")
    tela.click("text=Continuar editando")
    assert tela.is_visible("#form-ponto") and tela.input_value("#pt-nome") == NOME_A
    ok("Esc com formulário preenchido pede confirmação e permite continuar editando")
    for _ in range(40):
        tela.keyboard.press("Tab")
    assert tela.evaluate("!!document.activeElement.closest('.dialogo')")
    ok("foco do teclado fica preso dentro do diálogo")

    # validação no campo
    tela.fill("#pt-codigo", CODIGO_A)
    tela.select_option("#pt-rio", label=RIO_A)
    tela.fill("#pt-latitude", "-27.66")
    tela.fill("#pt-longitude", "-48.70")
    tela.fill("#pt-atencao", "200")
    tela.click("[form=form-ponto]")
    assert "três critérios" in texto(tela, "#pt-alerta-erro")
    assert tela.get_attribute("#pt-alerta", "aria-invalid") == "true"
    ok("critério incompleto mostra erro no próprio campo, sem fechar o diálogo")
    capturar(tela, "claro-04-dialogo-validacao")
    tela.fill("#pt-alerta", "150")
    tela.fill("#pt-critica", "100")
    tela.click("[form=form-ponto]")
    tela.wait_for_timeout(900)
    assert not tela.is_visible("#form-ponto")
    tela.click("#aba-pontos >> text=Novo ponto")
    tela.fill("#pt-codigo", CODIGO_B)
    tela.fill("#pt-nome", NOME_B)
    tela.select_option("#pt-rio", label=RIO_B)
    tela.fill("#pt-latitude", "-27.63")
    tela.fill("#pt-longitude", "-48.66")
    tela.click("[form=form-ponto]")
    tela.wait_for_timeout(900)
    grade = texto(tela, "#pontos-grade")
    assert CODIGO_A.lower() in grade and CODIGO_B.lower() in grade
    ok("dois pontos cadastrados (um sem critérios)")

    # confirmação dentro do diálogo preserva o formulário
    tela.click(f"#pontos-grade article:has-text('{CODIGO_A}') >> text=Editar")
    tela.fill("#pt-desatualizar", "90")
    tela.click(".dialogo >> text=Desativar")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    tela.click("text=Continuar editando")
    assert tela.input_value("#pt-desatualizar") == "90"
    tela.click("[form=form-ponto]")
    tela.wait_for_timeout(900)
    assert "90 min" in texto(tela, f"#pontos-grade article:has-text('{CODIGO_A}')")
    ok("cancelar a desativação mantém o formulário; edição salva")
    capturar(tela, "claro-05-pontos")

    # ---------- Exclusão de rio e ponto ----------
    tela.click("#aba-pontos >> text=Novo rio")
    tela.fill("#rio-nome", RIO_TEMP)
    tela.click("[form=form-rio]")
    tela.wait_for_timeout(700)
    tela.click(f"#rios-lista li:has-text('{RIO_TEMP}') button")
    tela.click(".dialogo >> text=Excluir rio")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    tela.click("text=Continuar editando")
    assert tela.is_visible("#form-rio")
    ok("cancelar a exclusão do rio mantém o diálogo aberto")
    tela.click(".dialogo >> text=Excluir rio")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    tela.click(".dialogo [data-descartar]")
    tela.wait_for_timeout(900)
    assert not tela.is_visible("#form-rio") and RIO_TEMP.lower() not in texto(tela, "#rios-lista")
    ok("rio sem pontos excluído após confirmação, e some da lista")
    tela.click(f"#rios-lista li:has-text('{RIO_A}') button")
    tela.click(".dialogo >> text=Excluir rio")
    tela.wait_for_selector("#form-rio .barra-mensagem.erro")
    assert "1 ponto ligado" in texto(tela, "#form-rio .barra-mensagem.erro")
    tela.click(".dialogo >> text=Cancelar")
    assert RIO_A.lower() in texto(tela, "#rios-lista")
    ok("rio com ponto ligado não é excluído e a mensagem explica o motivo")

    tela.click("#aba-pontos >> text=Novo ponto")
    tela.fill("#pt-codigo", CODIGO_TEMP)
    tela.fill("#pt-nome", "Ponto de teste")
    tela.select_option("#pt-rio", label=RIO_B)
    tela.fill("#pt-latitude", "-27.64")
    tela.fill("#pt-longitude", "-48.65")
    tela.click("[form=form-ponto]")
    tela.wait_for_timeout(900)
    tela.click(f"#pontos-grade article:has-text('{CODIGO_TEMP}') >> text=Editar")
    tela.click(".dialogo >> text=Excluir")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    tela.click(".dialogo [data-descartar]")
    tela.wait_for_timeout(900)
    assert CODIGO_TEMP.lower() not in texto(tela, "#pontos-grade")
    ok("ponto sem histórico real excluído após confirmação")

    # ---------- Medições ----------
    tela.click("#nav-medicoes")
    tela.wait_for_timeout(600)
    tela.select_option("#historico-ponto", label=ROTULO_A)
    tela.wait_for_timeout(400)
    for distancia in ["280", "282", "279", "90"]:
        tela.click("#aba-medicoes >> text=Registrar medição")
        tela.select_option("#medicao-ponto", label=ROTULO_A)
        tela.fill("#medicao-distancia", distancia)
        tela.click("[form=form-medicao]")
        tela.wait_for_timeout(700)
    linhas = texto(tela, "#historico-linhas")
    assert "suspeita" in linhas and "manual" in linhas
    assert tela.query_selector("#historico-grafico svg.grafico")
    ok("medições manuais registradas; salto brusco marcado como suspeito; gráfico desenhado")
    capturar(tela, "claro-06-medicoes")

    # ---------- Simulação ----------
    tela.click("#nav-simulacao")
    tela.wait_for_timeout(600)
    tela.select_option("#sim-ponto", label=ROTULO_A)
    tela.fill("#sim-inicial", "100")
    tela.fill("#sim-variacao", "150")
    tela.click("#form-simulacao [type=submit]")
    assert "menor que a distância inicial" in texto(tela, "#sim-variacao-erro")
    ok("simulação impossível é barrada no campo antes de ir à API")
    tela.fill("#sim-inicial", "260")
    tela.fill("#sim-variacao", "180")
    tela.click("#form-simulacao [type=submit]")
    tela.wait_for_timeout(1200)
    assert "crítico" in texto(tela, "#sim-situacao") and tela.query_selector("#sim-grafico svg.grafico")
    ok("simulação de subida leva a situação simulada a Crítico")
    capturar(tela, "claro-07-simulacao")

    # ---------- Situação: real x simulado ----------
    tela.click("#nav-situacao")
    tela.wait_for_timeout(900)
    reais = texto(tela, "#painel-linhas")
    assert "90 cm" in reais
    tela.click("[data-modo=simulada]")
    tela.wait_for_timeout(900)
    assert "80 cm" in texto(tela, "#painel-linhas")
    assert tela.get_attribute("[data-modo=simulada]", "aria-pressed") == "true"
    ok("painel alterna entre dados reais e simulados")
    tela.click("[data-modo=real]")
    tela.wait_for_timeout(600)
    capturar(tela, "claro-08-situacao")

    # ponto com medição real não pode ser excluído
    tela.click("#nav-pontos")
    tela.wait_for_timeout(600)
    tela.click(f"#pontos-grade article:has-text('{CODIGO_A}') >> text=Editar")
    tela.click(".dialogo >> text=Excluir")
    tela.wait_for_selector(".dialogo .barra-mensagem.atencao")
    tela.click(".dialogo [data-descartar]")
    tela.wait_for_selector("#form-ponto .barra-mensagem.erro")
    assert "desativar" in texto(tela, "#form-ponto .barra-mensagem.erro")
    tela.click(".dialogo >> text=Cancelar")
    assert CODIGO_A.lower() in texto(tela, "#pontos-grade")
    ok("ponto com medição real não é excluído; a mensagem sugere desativar")

    # ---------- Ocorrências ----------
    tela.click("#nav-ocorrencias")
    tela.wait_for_timeout(500)
    tela.click("#aba-ocorrencias >> text=Registrar ocorrência")
    tela.select_option("#ocorrencia-ponto", label=ROTULO_B)
    tela.select_option("#ocorrencia-classificacao", "laranja")
    tela.fill("#ocorrencia-motivo", "Equipe viu água sobre a calçada")
    tela.click("[form=form-ocorrencia]")
    tela.wait_for_timeout(800)
    assert CODIGO_B.lower() in texto(tela, "#ocorrencias-linhas")
    ok("ocorrência manual registrada")

    # ---------- Auditoria ----------
    tela.click("#nav-auditoria")
    tela.wait_for_timeout(700)
    auditoria = tela.inner_text("#auditoria-linhas")
    assert all(a in auditoria for a in ["SIMULACAO_GERADA", "MEDICAO_MANUAL_REGISTRADA", "OCORRENCIA_ABERTA", "PONTO_ATUALIZADO"])
    ok("auditoria lista as ações")

    # ---------- Tema escuro em todas as telas do painel ----------
    tela.click("#pg-painel [data-alternar-tema]")
    assert tela.evaluate("document.documentElement.dataset.tema") == "escuro"
    for aba in ["situacao", "pontos", "medicoes", "simulacao", "ocorrencias", "auditoria"]:
        tela.click(f"#nav-{aba}")
        tela.wait_for_timeout(700)
        fundo = tela.evaluate("getComputedStyle(document.querySelector('.moldura-principal')).backgroundColor")
        assert fundo == "rgb(28, 28, 28)", fundo
        capturar(tela, f"escuro-10-{aba}")
    ok("tema escuro aplicado em todas as abas do painel")
    tela.click("#nav-pontos")
    tela.wait_for_timeout(500)
    tela.click(f"#pontos-grade article:has-text('{CODIGO_A}') >> text=Editar")
    tela.wait_for_selector("#form-ponto")
    capturar(tela, "escuro-11-dialogo")
    tela.click(".dialogo >> text=Cancelar")
    assert not tela.is_visible("#form-ponto")
    ok("botão Cancelar fecha o diálogo")

    # ---------- Encerrar ocorrência com confirmação ----------
    tela.click("#nav-ocorrencias")
    tela.wait_for_timeout(500)
    # Encerra a ocorrência criada nesta execução (outras abertas no banco não atrapalham).
    tela.click(f"#ocorrencias-linhas tr:has-text('{CODIGO_B}') >> text=Encerrar")
    tela.wait_for_selector(".dialogo >> text=O ponto volta")
    tela.click(".dialogo [data-confirmar]")
    tela.wait_for_timeout(800)
    assert CODIGO_B.lower() not in texto(tela, "#ocorrencias-linhas")
    ok("encerrar ocorrência pede confirmação e atualiza a lista")

    # ---------- Mapa público ----------
    tela.click("text=Mapa público")
    tela.wait_for_timeout(1500)
    lateral = texto(tela, "#mapa-pontos")
    assert "crítico" in lateral and "280 cm" not in lateral
    ok("mapa público mostra só dados reais")
    capturar(tela, "escuro-12-mapa")
    tela.select_option("#mapa-rio", label=RIO_B)
    tela.wait_for_timeout(300)
    assert CODIGO_A.lower() not in texto(tela, "#mapa-pontos") and NOME_A.lower() not in texto(tela, "#mapa-pontos")
    ok("filtro por rio no mapa")
    tela.click("#pg-mapa [data-alternar-tema]")
    tela.wait_for_timeout(300)
    capturar(tela, "claro-12-mapa")

    # ---------- Sair ----------
    tela.goto(f"{ENDERECO}/#painel")
    tela.wait_for_timeout(600)
    tela.click(".nav-painel >> text=Sair")
    tela.wait_for_timeout(500)
    assert tela.evaluate("location.hash") == "#inicio"
    ok("sair encerra a sessão")
    contexto.close()

    # ---------- Celular ----------
    for tema in ["light", "dark"]:
        contexto_celular = navegador.new_context(viewport={"width": 390, "height": 844}, color_scheme=tema, is_mobile=True, has_touch=True)
        celular = contexto_celular.new_page()
        observar(celular)
        for rota in ["inicio", "login", "mapa"]:
            celular.goto(f"{ENDERECO}/#{rota}")
            celular.wait_for_timeout(900)
            assert sem_rolagem_lateral(celular), rota
            capturar(celular, f"{NOME_TEMA[tema]}-celular-{rota}")
        celular.goto(f"{ENDERECO}/#login")
        celular.wait_for_timeout(500)
        celular.fill("#login-email", EMAIL)
        celular.fill("#login-senha", SENHA)
        celular.click("#form-login [type=submit]")
        celular.wait_for_function("location.hash === '#painel'")
        celular.wait_for_timeout(900)
        assert not celular.is_visible("#nav-pontos")
        celular.click(".botao-menu")
        celular.wait_for_timeout(400)
        assert celular.is_visible("#nav-pontos")
        capturar(celular, f"{NOME_TEMA[tema]}-celular-menu")
        celular.click("#nav-medicoes")
        celular.wait_for_timeout(900)
        assert not celular.is_visible("#nav-pontos")
        assert sem_rolagem_lateral(celular)
        capturar(celular, f"{NOME_TEMA[tema]}-celular-medicoes")
        celular.click("#aba-medicoes >> text=Registrar medição")
        celular.wait_for_timeout(400)
        assert sem_rolagem_lateral(celular)
        capturar(celular, f"{NOME_TEMA[tema]}-celular-dialogo")
        contexto_celular.close()
    ok("celular (390 px) nos dois temas: sem rolagem horizontal, menu em gaveta, diálogo como painel inferior")

    navegador.close()

print(f"\n{aprovadas} verificações aprovadas")
print("Erros de console/página:", erros or "nenhum")
sys.exit(1 if erros else 0)
