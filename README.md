# FluviSense

Rede de micropontos de leitura de rios em Palhoça/SC.

Em cada ponto, um sensor instalado **acima** da água mede a distância até a superfície do rio. Quando a água sobe, essa distância diminui. O FluviSense:

- registra essas medições;
- confere se cada leitura é válida;
- mostra a situação de cada ponto num mapa público e num painel do operador;
- guarda o histórico.

A ideia é ampliar a quantidade de pontos acompanhados na cidade e servir de apoio aos órgãos de monitoramento hidrológico, que trabalham com poucas estações por município.

> O FluviSense não emite alertas oficiais. As cores dos pontos seguem critérios definidos pelo operador para cada ponto.

## Organização das pastas

```
FluviSense - Projeto Integrador/
├── README.md               este arquivo
├── api/                    servidor (Python + FastAPI + PostgreSQL)
│   ├── app/                rotas, regras, tabelas e validações
│   ├── migrations/         criação e atualização do banco, em SQL (001 a 006)
│   ├── scripts/            migrar.py (cria/atualiza o banco) e criar_operador.py
│   └── tests/              testes automáticos da API
├── site/                   interface (HTML, CSS e JavaScript)
│   ├── index.html          páginas: início, mapa, login e painel
│   ├── css/  js/  imagens/
│   └── tests/              teste da interface no navegador
├── documentos/
│   ├── gerar_documentos.py gera os diagramas PNG e os documentos Word a partir de tecnico/
│   ├── entrega/            documentos para a faculdade (gerados; não edite à mão)
│   └── tecnico/            documentação técnica (a fonte), diagramas e capturas de tela
└── .github/workflows/      testes automáticos no GitHub
```

## Tecnologias

| Parte | Tecnologia |
|---|---|
| API | Python 3.11 ou mais novo (testado com 3.11, 3.12 e 3.13), FastAPI, SQLAlchemy 2, Pydantic 2 |
| Banco | PostgreSQL (Supabase em produção; testado com PostgreSQL 16) |
| Site | HTML, CSS e JavaScript, sem etapa de compilação. Visual no estilo Microsoft Fluent 2, com tema claro e escuro. Mapa com Leaflet |
| Testes | pytest (API) e Playwright (interface) |

## Como executar no seu computador

Pré-requisitos: Python 3.11 ou mais novo e um banco PostgreSQL (local ou um projeto Supabase de teste).

### 1. Preparar a API (só na primeira vez)

No terminal, dentro da pasta do projeto:

```bash
cd api
python -m venv .venv
.venv\Scripts\activate              # no Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env              # no Mac/Linux: cp .env.example .env
```

Abra o arquivo `api/.env` e preencha:

- `DATABASE_URL`: a conexão com o PostgreSQL. No Supabase, use a opção **Session pooler**, no formato URI.
- `JWT_SECRET_KEY`: um texto aleatório com pelo menos 32 caracteres. Para gerar um, rode:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

  **Sem esse valor, a API não liga, de propósito.**

Depois, crie as tabelas e o operador:

```bash
python scripts/migrar.py
python scripts/criar_operador.py --email voce@exemplo.com --nome "Seu nome"
```

### 2. Ligar a API (terminal 1)

```bash
cd api
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

A documentação interativa da API fica em http://localhost:8001/docs.

### 3. Ligar o site (terminal 2)

```bash
cd site
python -m http.server 8080
```

Abra http://localhost:8080. Em `localhost`, o site usa automaticamente a API em `http://localhost:8001/api`.

## Testes

Na pasta `api`, com o ambiente ativado:

```bash
pytest                       # banco temporário SQLite
```

Para testar também as migrações num PostgreSQL de verdade, use um banco **descartável**: o teste apaga o conteúdo dele.

```bash
set TEST_DATABASE_URL=postgresql://usuario:senha@localhost:5432/fluvisense_teste   # Mac/Linux: export ...
pytest
```

Teste da interface (opcional). Ele grava rios, pontos e medições de teste, então use um banco **só para testes**, nunca o de produção:

1. Instale com `pip install playwright` e depois `playwright install chromium`.
2. Aponte o `DATABASE_URL` do `api/.env` para o banco de testes e, na pasta `api`, rode `python scripts/migrar.py` e `python scripts/criar_operador.py` (como no passo 1).
3. Ligue a API e o site (passos 2 e 3 acima).
4. Na pasta do projeto, informe o operador e rode:

   ```bash
   set FLUVISENSE_E2E_EMAIL=op@exemplo.com        # Mac/Linux: export ...
   set FLUVISENSE_E2E_PASSWORD=senha-do-operador
   python site/tests/test_interface.py resultado
   ```

As capturas de cada etapa ficam em `resultado/capturas`. Se o site não estiver em `http://localhost:8080`, informe o endereço em `FLUVISENSE_E2E_URL`. O teste usa nomes diferentes a cada execução e pode ser repetido no mesmo banco.

No GitHub, os testes rodam sozinhos a cada envio (`.github/workflows/testes.yml`).

## Publicação (Render + Supabase)

1. **Faça backup do banco antes de qualquer migração:** `pg_dump "$DATABASE_URL" > backup.sql`.
2. Rode `python scripts/migrar.py` com o `DATABASE_URL` de produção. As migrações criam tabelas, índices e restrições e ligam a RLS (005). A 006 troca os nomes das tabelas e colunas para português **sem apagar nenhum dado**: ela só renomeia. Para conferir o que já foi aplicado, use `python scripts/migrar.py --situacao`.
3. No Render, configure o serviço da API:
   - pasta raiz `api`;
   - comando de início `uvicorn app.main:app --host 0.0.0.0 --port $PORT`;
   - variáveis `DATABASE_URL`, `JWT_SECRET_KEY`, `APP_ENV=production` e `CORS_ORIGINS` (endereço do site). `JWT_EXPIRE_MINUTES` é opcional (padrão 480).
4. Publique a API e o site **juntos**: o site novo só conversa com a API nova (as rotas e os campos agora têm nomes em português).
5. No `site/index.html`, confira `enderecoApi` em `window.FLUVISENSE_CONFIGURACAO`. O serviço publicado no Render ainda se chama `hydrosys-api` (nome anterior do projeto); se ele for renomeado lá, troque o endereço aqui.

## Sensor enviando medições

1. No painel, abra o ponto em **Rios e pontos → Editar → Gerar chave do sensor**. A chave aparece uma única vez.
2. O dispositivo envia:

```bash
curl -X POST https://SUA-API/api/sensor/medicoes \
  -H "Content-Type: application/json" -H "X-Chave-Sensor: CHAVE_DO_PONTO" \
  -d '{"codigo_ponto": "CUB-01", "distancia_cm": 248.5, "medida_em": "2026-10-21T14:30:00-03:00"}'
```

A chave só vale para o próprio ponto. Sem `medida_em`, vale o horário de recebimento.

## Documentação

| Documento | Para quê |
|---|---|
| `documentos/entrega/` | Documento de Requisitos e Documento de Projeto em Word, gerados a partir dos arquivos abaixo |
| [Visão e escopo](documentos/tecnico/01-visao-e-escopo.md) | Problema, objetivo e o que o sistema faz |
| [Requisitos](documentos/tecnico/02-requisitos.md) | Requisitos, regras e critérios de aceitação ligados aos testes |
| [Arquitetura e dados](documentos/tecnico/03-arquitetura-e-dados.md) | Componentes, banco, diagramas e rotas da API |
| [Decisões](documentos/tecnico/04-decisoes.md) | Por que cada escolha foi feita |
| [Validação](documentos/tecnico/05-validacao.md) | Testes executados e resultados |

### Atualizar os documentos Word e os diagramas

Os arquivos de `documentos/entrega/` e os PNG de `documentos/tecnico/diagramas/` são gerados a partir dos arquivos Markdown de `documentos/tecnico/`. Para corrigir algo, edite o Markdown e rode, na pasta do projeto:

```bash
python documentos/gerar_documentos.py
```

O script precisa de [pandoc](https://pandoc.org/installing.html), do Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`) e do Playwright (`pip install playwright` e `playwright install chromium`). Essas ferramentas só são necessárias para gerar os documentos, não para rodar o sistema. Mudanças feitas direto no Word se perdem na próxima geração.
