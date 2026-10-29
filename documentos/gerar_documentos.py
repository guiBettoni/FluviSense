"""Gera os PNG dos diagramas e os documentos Word de entrega a partir da documentação técnica.

A fonte de tudo são os arquivos Markdown de documentos/tecnico (decisões D11 e D21):
- os diagramas Mermaid de 03-arquitetura-e-dados.md viram os PNG de documentos/tecnico/diagramas;
- 02-requisitos.md vira o Documento de Requisitos;
- 01-visao-e-escopo.md + 03-arquitetura-e-dados.md + 05-validacao.md viram o Documento de Projeto.

Por isso, nunca corrija o Word à mão: corrija o Markdown e rode este script de novo.

Ferramentas necessárias (só para quem for gerar os documentos, não para rodar o sistema):
- pandoc (https://pandoc.org);
- Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`, comando `mmdc`);
- Playwright para Python (`pip install playwright` e `playwright install chromium`).

Uso, a partir da pasta do projeto:
    python documentos/gerar_documentos.py            # diagramas e documentos Word
    python documentos/gerar_documentos.py --diagramas  # só os PNG
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent
TECNICO = DOCS / "tecnico"
DIAGRAMAS = TECNICO / "diagramas"
ENTREGA = DOCS / "entrega"
ARQUITETURA = TECNICO / "03-arquitetura-e-dados.md"

AUTOR = "Guilherme Bettoni Matiuzzi Pavão"
SUBTITULO = "Projeto Integrador · Análise e Desenvolvimento de Sistemas · FMP"
DATA = "Outubro de 2026"

DOCUMENTOS = [
    ("FluviSense - Documento de Requisitos.docx", "FluviSense: Documento de Requisitos", ["02-requisitos.md"]),
    ("FluviSense - Documento de Projeto.docx", "FluviSense: Documento de Projeto",
     ["01-visao-e-escopo.md", "03-arquitetura-e-dados.md", "05-validacao.md"]),
]


# ---------------------------------------------------------------- leitura dos blocos Mermaid

def blocos_mermaid(texto: str) -> list[str]:
    return re.findall(r"```mermaid\n(.*?)```", texto, flags=re.S)


def nome_do_diagrama(bloco: str) -> str:
    """Nome do PNG de cada bloco Mermaid de 03-arquitetura-e-dados.md."""
    primeira = bloco.strip().splitlines()[0].strip()
    if primeira.startswith("erDiagram"):
        return "modelo-dados"
    if primeira.startswith("classDiagram"):
        return "classes"
    if primeira.startswith("sequenceDiagram"):
        return "fluxo-medicao"
    if "Visitante" in bloco:
        return "casos-de-uso"
    return "componentes"


# ---------------------------------------------------------------- desenho em SVG (notação UML)

LH, HEAD, PAD = 21, 34, 8


class Caixa:
    def __init__(self, x, y, w, titulo, atributos, metodos=None, estereotipo=None):
        self.x, self.y, self.w = x, y, w
        self.titulo, self.atributos, self.metodos, self.estereotipo = titulo, atributos, metodos, estereotipo
        self.h = (HEAD + (14 if estereotipo else 0) + PAD * 2 + LH * len(atributos)
                  + ((PAD * 2 + LH * len(metodos)) if metodos is not None else 0))

    def linha(self, i):
        return self.y + HEAD + PAD + LH * i + LH / 2 - 2

    def lado(self, s, t=0.5):
        x, y, w, h = self.x, self.y, self.w, self.h
        return {"l": (x, y + h * t), "r": (x + w, y + h * t), "t": (x + w * t, y), "b": (x + w * t, y + h)}[s]

    def svg(self, fundo="#eef4fb", borda="#1f5fa8"):
        x, y, w = self.x, self.y, self.w
        hh = HEAD + (14 if self.estereotipo else 0)
        out = [f"<rect x='{x}' y='{y}' width='{w}' height='{self.h}' fill='white' stroke='{borda}' stroke-width='1.6'/>",
               f"<rect x='{x}' y='{y}' width='{w}' height='{hh}' fill='{fundo}' stroke='{borda}' stroke-width='1.6'/>"]
        ty = y + 22
        if self.estereotipo:
            out.append(f"<text x='{x + w / 2}' y='{y + 15}' text-anchor='middle' font-size='12' font-style='italic'>«{self.estereotipo}»</text>")
            ty += 12
        out.append(f"<text x='{x + w / 2}' y='{ty}' text-anchor='middle' font-size='16' font-weight='700'>{esc(self.titulo)}</text>")
        cy = y + hh + PAD
        for a in self.atributos:
            cy += LH
            out.append(f"<text x='{x + 10}' y='{cy - 5}' font-size='14'>{a}</text>")
        if self.metodos is not None:
            cy += PAD
            out.append(f"<line x1='{x}' y1='{cy}' x2='{x + w}' y2='{cy}' stroke='{borda}' stroke-width='1.2'/>")
            cy += PAD
            for m in self.metodos:
                cy += LH
                out.append(f"<text x='{x + 10}' y='{cy - 5}' font-size='14'>{esc(m)}</text>")
        return "".join(out)


def esc(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ligacao(pontos, tracejada=False, seta=False, rot1="", rot2="", rotulo="", pos_rotulo=None):
    d = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(pontos))
    s = (f"<path d='{d}' fill='none' stroke='#333' stroke-width='1.4'"
         f"{' stroke-dasharray=\"6 4\"' if tracejada else ''}{' marker-end=\"url(#seta)\"' if seta else ''}/>")
    for (px, py), (qx, qy), texto in ((pontos[0], pontos[1], rot1), (pontos[-1], pontos[-2], rot2)):
        if texto:
            ox = 8 if qx >= px else -26
            s += f"<text x='{px + ox}' y='{py - 6}' font-size='14'>{texto}</text>"
    if rotulo:
        rx, ry = pos_rotulo
        s += f"<text x='{rx}' y='{ry}' font-size='13' font-style='italic'>{rotulo}</text>"
    return s


def salvar_png(nome, largura, altura, partes):
    from playwright.sync_api import sync_playwright

    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{largura}' height='{altura}' font-family='Arial, sans-serif' fill='#222'>"
           "<defs><marker id='seta' viewBox='0 0 10 10' refX='10' refY='5' markerWidth='9' markerHeight='9' orient='auto-start-reverse'>"
           "<path d='M0,0 L10,5 L0,10' fill='none' stroke='#333' stroke-width='1.5'/></marker></defs>"
           f"<rect width='100%' height='100%' fill='white'/>{''.join(partes)}</svg>")
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": largura, "height": altura}, device_scale_factor=2)
        pagina.set_content(f"<html><body style='margin:0'>{svg}</body></html>")
        pagina.screenshot(path=str(DIAGRAMAS / f"{nome}.png"))
        navegador.close()


def ator(x, y, nome):
    return (f"<g stroke='#222' stroke-width='2.2' fill='none'><circle cx='{x}' cy='{y - 48}' r='14'/>"
            f"<line x1='{x}' y1='{y - 34}' x2='{x}' y2='{y + 6}'/><line x1='{x - 22}' y1='{y - 20}' x2='{x + 22}' y2='{y - 20}'/>"
            f"<line x1='{x}' y1='{y + 6}' x2='{x - 18}' y2='{y + 36}'/><line x1='{x}' y1='{y + 6}' x2='{x + 18}' y2='{y + 36}'/></g>"
            f"<text x='{x}' y='{y + 60}' text-anchor='middle' font-size='17' font-weight='600'>{nome}</text>")


def caso(x, y, texto, rx=140, ry=28):
    return (f"<ellipse cx='{x}' cy='{y}' rx='{rx}' ry='{ry}' fill='#eef4fb' stroke='#1f5fa8' stroke-width='1.8'/>"
            f"<text x='{x}' y='{y + 5}' text-anchor='middle' font-size='15'>{esc(texto)}</text>")


def desenhar_casos_de_uso(bloco: str):
    """Lê as linhas `ATOR --> UCn[Texto]` e desenha o diagrama UML."""
    atores = dict(re.findall(r"^\s*(\w+)\(\((.+?)\)\)", bloco, flags=re.M))
    casos: dict[str, list[str]] = {}
    for sigla, texto in re.findall(r"^\s*(\w+)\s*-->\s*\w+\[(.+?)\]", bloco, flags=re.M):
        casos.setdefault(atores[sigla], []).append(texto)
    operador = casos.pop("Operador")
    outros = list(casos.items())  # Visitante e Sensor, à direita
    ys = [100 + i * 78 for i in range(len(operador))]
    altura = ys[-1] + 80
    partes = [f"<rect x='280' y='20' width='660' height='{altura - 35}' rx='6' fill='#fafafa' stroke='#555' stroke-width='1.6'/>"
              "<text x='610' y='50' text-anchor='middle' font-size='18' font-weight='700'>FluviSense</text>"]
    oy = (ys[0] + ys[-1]) / 2
    for y in ys:
        partes.append(ligacao([(155, oy - 20), (360, y)]))
    for texto, y in zip(operador, ys):
        partes.append(caso(500, y, texto))
    partes.append(ator(130, oy, "Operador"))
    for i, (nome, textos) in enumerate(outros):
        y = ys[0] + 100 + i * (ys[-1] - ys[0] - 100)
        partes.append(ligacao([(1065, y - 20), (920, y)]))
        partes.append(caso(795, y, textos[0], rx=125, ry=34))
        partes.append(ator(1090, y + 20, nome))
    salvar_png("casos-de-uso", 1200, altura, partes)


def ler_classes(bloco: str):
    """Lê `class Nome { ... }` e `class apelido["rótulo"] { <<estereótipo>> ... }`."""
    classes = {}
    for chave, rotulo, corpo in re.findall(r'class (\w+)(?:\["(.+?)"\])?\s*\{(.*?)\}', bloco, flags=re.S):
        linhas = [l.strip() for l in corpo.strip().splitlines() if l.strip()]
        estereotipo = None
        if linhas and linhas[0].startswith("<<"):
            estereotipo = linhas.pop(0).strip("<>")
        atributos = [l for l in linhas if "(" not in l]
        metodos = [re.sub(r"\) (\w+)$", r"): \1", l) for l in linhas if "(" in l]
        classes[chave] = (rotulo or chave, atributos, metodos, estereotipo)
    return classes


def desenhar_classes(bloco: str):
    c = ler_classes(bloco)

    def caixa(chave, x, y, w):
        rotulo, atributos, metodos, estereotipo = c[chave]
        if estereotipo:
            return Caixa(x, y, w, rotulo, [], metodos, estereotipo)
        return Caixa(x, y, w, rotulo, atributos)

    rio = caixa("Rio", 40, 40, 250)
    ponto = caixa("PontoMonitoramento", 380, 40, 360)
    medicao = caixa("Medicao", 860, 40, 330)
    ocorrencia = caixa("Ocorrencia", 860, 360, 330)
    usuario = caixa("Usuario", 40, 220, 250)
    auditoria = caixa("EventoAuditoria", 40, 470, 250)
    servico = caixa("medicoes_py", 380, 560, 640)
    simulacao = caixa("simulacao_py", 380, 560 + servico.h + 30, 640)
    dados = [rio, ponto, medicao, ocorrencia, usuario, auditoria]
    partes = [b.svg() for b in dados] + [b.svg("#f4f4f4", "#555") for b in (servico, simulacao)]
    partes += [
        ligacao([rio.lado("r", 0.5), ponto.lado("l", 0.13)], rot1="1", rot2="0..*"),
        ligacao([ponto.lado("r", 0.2), medicao.lado("l", 0.25)], rot1="1", rot2="0..*"),
        ligacao([ponto.lado("r", 0.75), ocorrencia.lado("l", 0.5)], rot1="1", rot2="0..*"),
        ligacao([servico.lado("t", 0.3), ponto.lado("b", 0.3)], tracejada=True, seta=True, rotulo="usa",
                pos_rotulo=(servico.x + servico.w * 0.3 + 8, servico.y - 30)),
        ligacao([(servico.x + servico.w, servico.y + 40), (1225, servico.y + 40), (1225, medicao.y + 150),
                 (medicao.x + medicao.w, medicao.y + 150)], tracejada=True, seta=True, rotulo="cria",
                pos_rotulo=(1232, (servico.y + medicao.y + 190) / 2)),
    ]
    salvar_png("classes", 1280, simulacao.y + simulacao.h + 30, partes)


def ler_tabelas(bloco: str):
    tabelas = {}
    for nome, corpo in re.findall(r"^\s*(\w+) \{\n(.*?)^\s*\}", bloco, flags=re.S | re.M):
        colunas = []
        for linha in corpo.strip().splitlines():
            partes = re.sub(r'"[^"]*"', "", linha).split()
            tipo, coluna, chave = partes[0], partes[1], (partes[2] if len(partes) > 2 else "")
            colunas.append((chave, coluna, tipo))
        tabelas[nome] = colunas
    relacoes = re.findall(r"^\s*(\w+) \S+ (\w+) :", bloco, flags=re.M)
    return tabelas, relacoes


def desenhar_modelo_de_dados(bloco: str):
    tabelas, relacoes = ler_tabelas(bloco)
    posicoes = {"rios": (40, 40), "usuarios": (40, 260), "eventos_auditoria": (40, 520),
                "pontos_monitoramento": (420, 40), "medicoes": (880, 40), "ocorrencias": (880, 400)}
    caixas = {}
    for nome, (x, y) in posicoes.items():
        linhas = [f"{chave + ' ' if chave else ''}{coluna}  <tspan fill='#666'>{tipo}</tspan>"
                  for chave, coluna, tipo in tabelas[nome]]
        caixas[nome] = Caixa(x, y, 380 if nome == "pontos_monitoramento" else 330, nome, linhas)
    faltando = set(tabelas) - set(posicoes)
    if faltando:
        sys.exit(f"Tabela sem posição no desenho: {', '.join(sorted(faltando))}. Inclua em `posicoes`.")
    partes = [c.svg() for c in caixas.values()]
    for pai, filho in relacoes:
        p, f = caixas[pai], caixas[filho]
        i_fk = next(i for i, (chave, _, _) in enumerate(tabelas[filho]) if chave == "FK")
        x_meio = p.x + p.w + 40
        partes.append(ligacao([(p.x + p.w, p.linha(0)), (x_meio, p.linha(0)), (x_meio, f.linha(i_fk)), (f.x, f.linha(i_fk))],
                              rot1="1", rot2="N"))
    altura = max(c.y + c.h for c in caixas.values()) + 40
    salvar_png("modelo-dados", 1260, int(altura), partes)


def renderizar_mermaid(nome: str, bloco: str):
    mmdc = shutil.which("mmdc")
    if not mmdc:
        sys.exit("Comando mmdc não encontrado. Instale com: npm install -g @mermaid-js/mermaid-cli")
    with tempfile.TemporaryDirectory() as tmp:
        fonte = Path(tmp) / f"{nome}.mmd"
        fonte.write_text(bloco, encoding="utf-8")
        subprocess.run([mmdc, "-i", str(fonte), "-o", str(DIAGRAMAS / f"{nome}.png"), "-w", "1600", "-s", "2", "-b", "white"],
                       check=True, capture_output=True)


def gerar_diagramas():
    DIAGRAMAS.mkdir(exist_ok=True)
    desenhos = {"casos-de-uso": desenhar_casos_de_uso, "classes": desenhar_classes, "modelo-dados": desenhar_modelo_de_dados}
    for bloco in blocos_mermaid(ARQUITETURA.read_text(encoding="utf-8")):
        nome = nome_do_diagrama(bloco)
        if nome in desenhos:
            desenhos[nome](bloco)
        else:
            renderizar_mermaid(nome, bloco)
        print(f"diagrama: {nome}.png")


# ---------------------------------------------------------------- documentos Word

FILTRO_LUA = r"""
-- Blocos Mermaid viram a imagem PNG correspondente; links para outros .md viram só texto.
local function nome(texto)
  local primeira = texto:match("^%s*(%S+)")
  if primeira == "erDiagram" then return "modelo-dados" end
  if primeira == "classDiagram" then return "classes" end
  if primeira == "sequenceDiagram" then return "fluxo-medicao" end
  if texto:find("Visitante") then return "casos-de-uso" end
  return "componentes"
end
local legendas = {
  ["componentes"] = "Componentes do sistema",
  ["modelo-dados"] = "Modelo de dados",
  ["classes"] = "Diagrama de classes",
  ["casos-de-uso"] = "Diagrama de casos de uso",
  ["fluxo-medicao"] = "Fluxo de uma medição",
}
function CodeBlock(el)
  if el.classes[1] == "mermaid" then
    local n = nome(el.text)
    local imagem = pandoc.Image({pandoc.Str(legendas[n])}, "diagramas/" .. n .. ".png")
    if pandoc.Figure then
      return pandoc.Figure(pandoc.Plain({imagem}), {pandoc.Str(legendas[n])})
    end
    return pandoc.Para({imagem})
  end
end
function Table(tbl)
  -- Tabelas ocupam a largura da página; cada coluna recebe largura proporcional ao seu texto.
  local n = #tbl.colspecs
  local soma = {}
  for i = 1, n do soma[i] = 4 end
  local function contar(linhas)
    for _, linha in ipairs(linhas) do
      for i, celula in ipairs(linha.cells) do
        if i <= n then soma[i] = soma[i] + math.min(#pandoc.utils.stringify(celula.contents), 160) end
      end
    end
  end
  contar(tbl.head.rows)
  for _, corpo in ipairs(tbl.bodies) do contar(corpo.body) end
  local total = 0
  for i = 1, n do soma[i] = math.sqrt(soma[i]); total = total + soma[i] end
  for i = 1, n do
    local largura = math.max(soma[i] / total, 0.08)
    tbl.colspecs[i] = {tbl.colspecs[i][1], largura}
  end
  return tbl
end
function Link(el)
  if el.target:match("%.md") then return el.content end
end
function Para(el)
  -- Nota sobre a fonte dos diagramas: só faz sentido para quem lê o Markdown.
  if pandoc.utils.stringify(el):match("^Os diagramas deste arquivo estão em Mermaid") then return {} end
  -- Imagem sozinha no parágrafo (as capturas de tela) ganha legenda com o texto alternativo.
  if #el.content == 1 and el.content[1].t == "Image" and pandoc.Figure then
    local imagem = el.content[1]
    return pandoc.Figure(pandoc.Plain({imagem}), {pandoc.Str(pandoc.utils.stringify(imagem.caption))})
  end
end
"""


# Estilos que o pandoc cria com nome em inglês. Os estilos padrão do Word (Título 1, Normal etc.)
# já aparecem traduzidos no Word em português; estes não, porque não são do Word.
ESTILOS_EM_PORTUGUES = {
    "First Paragraph": "Primeiro parágrafo",
    "Compact": "Compacto",
    "Image Caption": "Legenda da imagem",
    "Captioned Figure": "Figura com legenda",
    "Figure": "Figura",
    "Table Caption": "Legenda da tabela",
    "Author": "Autor",
    "Date": "Data",
    "Abstract": "Resumo",
    "Abstract Title": "Título do resumo",
    "Source Code": "Código-fonte",
    "Verbatim Char": "Código no texto",
    "Definition": "Definição",
    "Definition Term": "Termo definido",
    "Section Number": "Número da seção",
}


def ajustar_word(docx: Path):
    """Acertos que o pandoc não faz sozinho.

    - pede ao Word para montar o sumário ao abrir (o pandoc deixa o campo vazio);
    - deixa o idioma do documento todo em português do Brasil;
    - traduz os nomes dos estilos criados pelo pandoc;
    - declara o tipo das imagens PNG, como o Word espera.
    """
    with zipfile.ZipFile(docx) as origem:
        conteudo = {nome: origem.read(nome) for nome in origem.namelist()}
    ajustes = conteudo["word/settings.xml"].decode("utf-8")
    if "w:updateFields" not in ajustes:
        ajustes = re.sub(r"(<w:settings[^>]*>)", r'\1<w:updateFields w:val="true" />', ajustes, count=1)
    ajustes = re.sub(r'(<w:themeFontLang w:val=")[^"]*(")', r"\1pt-BR\2", ajustes)
    conteudo["word/settings.xml"] = ajustes.encode("utf-8")
    estilos = conteudo["word/styles.xml"].decode("utf-8")
    estilos = re.sub(r'w:eastAsia="en-US"', 'w:eastAsia="pt-BR"', estilos)
    for ingles, portugues in ESTILOS_EM_PORTUGUES.items():
        estilos = estilos.replace(f'<w:name w:val="{ingles}" />', f'<w:name w:val="{portugues}" />')
    conteudo["word/styles.xml"] = estilos.encode("utf-8")
    tipos = conteudo["[Content_Types].xml"].decode("utf-8")
    if 'Extension="png"' not in tipos:
        tipos = tipos.replace("<Default ", '<Default Extension="png" ContentType="image/png" /><Default ', 1)
        conteudo["[Content_Types].xml"] = tipos.encode("utf-8")
    with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as destino:
        for nome, dados in conteudo.items():
            destino.writestr(nome, dados)


def gerar_word():
    pandoc = shutil.which("pandoc")
    if not pandoc:
        sys.exit("Comando pandoc não encontrado. Instale em https://pandoc.org/installing.html")
    with tempfile.TemporaryDirectory() as tmp:
        filtro = Path(tmp) / "filtro.lua"
        filtro.write_text(FILTRO_LUA, encoding="utf-8")
        for arquivo, titulo, fontes in DOCUMENTOS:
            subprocess.run([
                pandoc, *[str(TECNICO / f) for f in fontes],
                "-o", str(ENTREGA / arquivo),
                "--from", "gfm", "--toc", "--toc-depth=2",
                "--lua-filter", str(filtro),
                "--resource-path", str(TECNICO),
                "-M", f"title={titulo}", "-M", f"subtitle={SUBTITULO}", "-M", f"author={AUTOR}", "-M", f"date={DATA}",
                "-M", "lang=pt-BR", "-M", "toc-title=Sumário",
            ], check=True)
            ajustar_word(ENTREGA / arquivo)
            print(f"documento: {arquivo}")


def main():
    parser = argparse.ArgumentParser(description="Gera os diagramas e os documentos Word do FluviSense.")
    parser.add_argument("--diagramas", action="store_true", help="Gera só os PNG dos diagramas.")
    args = parser.parse_args()
    gerar_diagramas()
    if not args.diagramas:
        gerar_word()


if __name__ == "__main__":
    main()
