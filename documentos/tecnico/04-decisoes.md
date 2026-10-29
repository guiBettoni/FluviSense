# Decisões e histórico de mudanças

## Histórico resumido

| Quando | O que aconteceu | Evidência |
|---|---|---|
| Início de 2026.1 | Ideia inicial "AlagaAlerta Palhoça" (EAD 01) | `EAD 01 - Visão de produto.docx` |
| Maio de 2026 | Protótipo com dados no navegador, login fixo no código e servidor SQLite (o servidor não foi preservado) | pasta `hydroSys/` do ZIP de outubro |
| ~30/05/2026 | MVP com FastAPI + PostgreSQL/Supabase, publicado no Render | código `hydro-sys-main`, cache `v=20260530-mvp` |
| Junho de 2026 | Requisitos (26 RF), casos de uso, diagrama de classes, MER MySQL de 16 tabelas e AV2 do PI1 | documentos da pasta `Entrega Final/` |
| 21/10/2026 | Versão 2.0: escopo reduzido ao monitoramento por distância, modelo de dados novo, testes e documentação reescrita | este repositório |
| 28/10/2026 | Projeto renomeado de HydroSys para FluviSense; tudo em português do Brasil; diagramas e documentos de entrega refeitos | este repositório (ver [D20](#d20)) |
| 28/10/2026 | Banco, modelos, rotas e campos da API com nomes em português, com migração que só renomeia; nomes de convenção das ferramentas mantidos | este repositório (ver [D22](#d22)) |

Os materiais da versão 1 (2026.1) ficam fora deste repositório, em arquivo privado do autor. A coluna "Evidência" cita esses arquivos pelo nome que tinham na época.

O MER de junho nunca foi implementado: o MVP usava 7 tabelas próprias. A versão 2.0 partiu do código que estava em uso, e não do MER.

## Decisões da versão 2.0

<a id="d1"></a>
**D1. Escopo reduzido ao monitoramento.** Ficaram fora: moradores, WhatsApp, abrigos, pedidos de ajuda e alerta público. Motivo: nada disso funcionava de ponta a ponta, e o cadastro de moradores guardava dados pessoais sem uso. O código dessas telas foi removido; a correspondência com os requisitos está em [Requisitos](02-requisitos.md#correspondência-com-os-requisitos-de-20261).

<a id="d2"></a>
**D2. Distância como grandeza principal.** O sensor mede a distância até a água. Converter para nível exige a altura de instalação numa referência conhecida, que não existe. Gravar um "nível" calculado sem essa base seria apresentar um valor inventado como observado.

<a id="d3"></a>
**D3. Ponto e sensor na mesma tabela.** Hoje cada ponto tem um sensor, e nenhum requisito pede trocar o aparelho mantendo o histórico, nem colocar dois sensores no mesmo ponto. Separar agora só acrescentaria junções. Quando isso for necessário, a chave do sensor e os parâmetros técnicos saem para uma tabela `sensores_ponto` (o nome `sensores` já é o da tabela antiga do MVP).

<a id="d4"></a>
**D4. Rio como tabela.** É barato, evita nomes digitados de formas diferentes e permite filtrar por rio.

<a id="d5"></a>
**D5. Critérios configuráveis e provisórios.** O FluviSense não traz nenhum limiar padrão: a classificação só existe quando o operador informa as três distâncias. Todo critério nasce marcado como provisório, e a interface mostra isso.

<a id="d6"></a>
**D6. Nova regra para leituras bruscas (substitui o RNF08 antigo).** A regra antiga comparava cada leitura com a média das 3 últimas *aceitas* e descartava a leitura se a diferença passasse de 50%. Nos testes de outubro, uma subida real de 10 para 130 cm foi toda descartada e o mapa continuou verde, porque as leituras descartadas nunca entravam na média. A regra nova:

- separa **inválida** (fisicamente impossível) de **suspeita** (salto brusco);
- guarda e exibe a leitura suspeita com aviso, em vez de escondê-la;
- usa a **mediana** das 3 últimas não inválidas, incluindo as suspeitas.

Resultado: um pico isolado não muda a referência, e uma mudança que se mantém é confirmada na 3ª leitura. O limite de 50% foi mantido como padrão porque vinha do requisito original. Cada ponto pode trocar esse limite por um valor em cm.

<a id="d7"></a>
**D7. Leitura suspeita aparece na situação.** Entre esconder uma subida real e mostrar um possível falso positivo marcado como "suspeita", a segunda opção é a mais segura para um sistema de acompanhamento.

<a id="d8"></a>
**D8. Dado antigo não confirma a condição atual.** Passado o prazo do ponto (padrão de 12 h, vindo da RN05 antiga), a situação exibida vira "Desatualizado", mesmo que a última medição estivesse normal.

<a id="d9"></a>
**D9. Real e simulado separados pela origem.** O fluxo é definido pela coluna `origem` de cada medição, e cada fluxo tem sua referência e sua situação. O mapa público só lê o fluxo real. A simulação é feita na API, por cenário, para que passe pela mesma validação dos dados reais e possa ser testada.

<a id="d10"></a>
**D10. Sensor com chave por ponto.** No protótipo de maio havia um token fixo para os sensores. No MVP de junho a rota de leituras ficou aberta: qualquer pessoa podia mudar o mapa público. Agora cada ponto tem sua chave, guardada só como hash. A rota está pronta para o hardware, mas a integração física não faz parte desta versão.

<a id="d11"></a>
**D11. Diagramas em texto (Mermaid) como fonte.** Os arquivos Astah (`.asta`) e o modelo do MySQL Workbench precisam de programas próprios para editar, e a fonte do MER (`.mwb`) nem estava no projeto. Os diagramas da versão 2.0 ficam em [Arquitetura e dados](03-arquitetura-e-dados.md), em texto versionado junto com o código, para que uma mudança no sistema e no diagrama apareçam na mesma revisão. As imagens PNG são geradas a partir deles (ver [D21](#d21)). O Mermaid não tem notação UML de casos de uso e mostra classes e tabelas de forma pouco legível quando impressas; por isso esses três PNG são desenhados por `documentos/gerar_documentos.py` com o mesmo conteúdo do texto. Os diagramas antigos não fazem parte deste repositório.

<a id="d12"></a>
**D12. Tabelas novas em vez de alterar as antigas.** As tabelas do MVP tinham significado diferente (nível de água e limiares de nível). Reaproveitar as colunas deixaria dados antigos com sentido errado. A migração 004 cria tabelas novas, copia o que dá para aproveitar e não altera nem apaga as antigas.

<a id="d13"></a>
**D13. Um operador ativo.** A regra já existia na migração 002 e foi mantida para não mudar o banco de produção sem necessidade. Para ter mais operadores, basta remover o índice `usuarios_um_operador_ativo_idx` numa nova migração.

<a id="d14"></a>
**D14. Migrações em SQL puro com um executor simples.** Em vez de adotar Alembic, o `scripts/migrar.py` (cerca de 100 linhas) aplica os arquivos em ordem e registra cada um. É suficiente para o tamanho do projeto e mantém o padrão dos arquivos 002 e 003 que já existiam.

<a id="d15"></a>
**D15. Interface no estilo Microsoft Fluent 2, sem biblioteca externa.** O site continua em HTML, CSS e JavaScript, sem etapa de compilação. O Fluent foi aplicado como um conjunto de tokens em CSS (cores, tipografia Segoe UI, espaçamento de 4 px, raios, sombras e movimento) e componentes próprios, em vez de adotar React ou Fluent UI Web Components, para não reescrever a aplicação nem acrescentar dependências.

O tema claro/escuro segue o sistema operacional na primeira visita e guarda a escolha do usuário. O Google Fonts e a animação de chuva foram retirados; a marca passou a usar o ícone da gota com o nome em texto, porque o logotipo antigo tinha letras brancas e sumia no tema claro.

<a id="d16"></a>
**D16. Formulário não fecha por acidente.** Diálogos com formulário só fecham por Cancelar, pelo X, ao salvar ou pelo Esc. Se algo foi preenchido, o Esc pergunta antes de descartar, e clicar fora do diálogo não faz nada. Confirmações pedidas de dentro de um formulário (como desativar ponto) aparecem no próprio diálogo, para não perder o que foi digitado.

<a id="d17"></a>
**D17. Exclusão só quando não apaga histórico.** Rios e pontos ganharam exclusão, mas respeitando o RNF04:

- **Rio:** só pode ser excluído sem nenhum ponto ligado, contando os desativados. Isso evita pontos sem rio.
- **Ponto:** só pode ser excluído se não tiver medição real nem ocorrência. É o caso de um ponto cadastrado por engano ou usado só em simulação. As medições simuladas dele saem junto. Ponto com histórico real continua com o caminho de antes: desativar.

A rota `DELETE /api/pontos/{id}` continua desativando. A exclusão definitiva tem uma rota própria (`DELETE /api/pontos/{id}/definitivo`), para que um clique antigo ou um script não apague um ponto sem querer.

Na interface, "Excluir" fica dentro do diálogo de edição, junto do "Desativar", e não como botão a mais na lista. A confirmação aparece no próprio diálogo. Se a exclusão for recusada, a mensagem explica o motivo e o que fazer.

<a id="d18"></a>
**D18. Pastas organizadas por finalidade.** A raiz do projeto agora separa `api/` (antigo `backend/`), `site/` (antigo `frontend/`) e `documentos/`. Dentro de `documentos/` ficam as entregas da faculdade e a documentação técnica (o histórico de 2026.1 também ficava ali e saiu na [D20](#d20)). Os nomes de pasta mudaram, mas os arquivos de dentro continuam iguais. No Render, a pasta raiz do serviço da API precisa passar de `backend` para `api`.

<a id="d19"></a>
**D19. Endurecimento de segurança.**
- A API não liga sem um `JWT_SECRET_KEY` de pelo menos 32 caracteres. Antes havia um segredo padrão no código público.
- O login bloqueia por 15 minutos depois de 5 senhas erradas seguidas para o mesmo e-mail.
- A migração 005 liga a RLS do PostgreSQL em todas as tabelas, para a API automática do Supabase não expor dados.
- O Leaflet é carregado com verificação de integridade (SRI).

<a id="d20"></a>
**D20. Novo nome e tudo em português.** O projeto passou a se chamar **FluviSense** (antes, HydroSys). Mudou o nome no site, na API, nos scripts, nas variáveis de ambiente (`FLUVISENSE_*`), na documentação e no repositório. Todo texto que aparece para o usuário, os comentários, as mensagens de erro da API e os diagramas estão em português do Brasil. Nesta etapa, os nomes técnicos (tabelas, colunas, rotas e variáveis do código) ainda ficaram em inglês; a [D22](#d22) os passou para português. Os materiais da versão 1 (documentos, apresentação, protótipo e diagramas Astah) saíram do repositório porque citam outras pessoas e têm credenciais de teste fixas; ficam em arquivo privado.

Efeitos para quem já tem o sistema no ar: as chaves salvas no navegador (`hydrosys_*`) mudaram para `fluvisense_*`, então o operador faz login de novo uma vez e o tema volta ao padrão; a variável `HYDROSYS_OPERATOR_PASSWORD` virou `FLUVISENSE_OPERATOR_PASSWORD`. O endereço da API publicada no Render só muda se o serviço for renomeado lá.

<a id="d21"></a>
**D21. Documentos Word gerados a partir da documentação técnica.** Os documentos de entrega (`documentos/entrega/`) não são escritos à mão: `documentos/gerar_documentos.py` monta cada um a partir dos arquivos Markdown desta pasta e gera também os PNG dos diagramas. O Documento de Requisitos vem de `02-requisitos.md`; o Documento de Projeto junta `01-visao-e-escopo.md`, `03-arquitetura-e-dados.md` e `05-validacao.md`. Motivo: na revisão de 28/10/2026, a versão anterior dos arquivos Word citava números de testes antigos, um diagrama de casos de uso cortado e o sumário com título em inglês; com uma fonte só, corrigir o Markdown e rodar o script atualiza tudo. Por isso, uma mudança feita direto no Word se perde na próxima geração: a correção deve ser feita no Markdown.

<a id="d22"></a>
**D22. Banco e regras do sistema com nomes em português; padrões das ferramentas mantidos.** O MVP de 2026.1 foi escrito com tabelas e colunas em inglês (`sensors`, `residents`, `app_users`), e a versão 2.0 seguiu esse padrão. O autor é brasileiro, os requisitos usam termos em português, e ter dois vocabulários obrigava a manter uma tabela de tradução entre o documento e o código. Por isso passaram para português:

- tabelas, colunas, restrições, índices e sequências do banco (migração 006);
- o que nasce do banco ou das regras do projeto: modelos e esquemas (`modelos.py`, `esquemas.py`), rotas da API e campos do JSON (por exemplo, `POST /api/sensor/medicoes` com `codigo_ponto`, `distancia_cm` e `medida_em`), serviços (`servicos/medicoes.py`) e o código do site.

Ficou com o nome padrão de fábrica tudo o que é convenção de ferramenta, porque quem conhece FastAPI, pytest ou Render espera encontrar esses nomes, e trocá-los não ajuda ninguém a entender o projeto:

| Nome mantido | Padrão de onde vem |
|---|---|
| Variáveis de ambiente `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`, `APP_ENV` (`development`/`production`), `CORS_ORIGINS`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `TEST_DATABASE_URL` | Nomes usados pela documentação do FastAPI, do SQLAlchemy e de serviços como Render e Supabase. |
| Pasta `app/`, arquivo `main.py` e objeto `app` (comando `uvicorn app.main:app`) | Estrutura padrão de um projeto FastAPI. |
| Pastas `tests/` e `migrations/`; arquivos `test_*.py` e funções `test_*` | O pytest só encontra os testes com esses prefixos sem configuração extra. |
| `requirements.txt`, `conftest.py`, `.env`, `.gitignore`, `README.md`, `LICENSE` | Nomes que o pip, o pytest, o Git e o GitHub procuram. |
| Palavras das linguagens e funções das bibliotecas (`def`, `select`, `model_config`, `L.map`) | Fazem parte do Python, do SQL, do JavaScript e das bibliotecas. |
| Cabeçalhos `Authorization: Bearer`, `Content-Type` e `Retry-After`; campos `sub`, `iat`, `exp` do token | Padrões HTTP e JWT. |
| `prefers-color-scheme`, `light` e `dark` no CSS; classes do VLibras | Padrão CSS e nomes que o script do VLibras procura. |

Como foi feito sem perder dados: a 006 só renomeia. Ela confere se o nome antigo existe antes de trocar, então pode ser aplicada num banco novo ou no do Supabase. O único valor alterado é o perfil `OPERATOR`, que virou `OPERADOR`. As migrações 001 a 005 continuam com o conteúdo original, porque registram o que já foi executado; só os nomes dos arquivos mudaram, e o `scripts/migrar.py` reconhece os nomes antigos para não aplicar nada duas vezes.

Efeitos para quem já tem o sistema no ar:

1. Fazer backup do banco e rodar `python scripts/migrar.py` (aplica a 006).
2. No Render, o comando de início (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) e as variáveis de ambiente continuam os mesmos.
3. Publicar a API e o site ao mesmo tempo, porque as rotas e os campos do JSON mudaram.
4. O operador entra de novo uma vez (o token antigo tinha o perfil `OPERATOR`).
5. Um sensor já configurado precisa usar a nova rota e o novo cabeçalho (`X-Chave-Sensor`). A chave dele continua valendo.

## Arquivos removidos ou substituídos

Os caminhos abaixo são os da época, antes da reorganização D18.

| Arquivo | Destino |
|---|---|
| `frontend/js/abrigos.js`, `doacoes.js`, `emergencia.js` | Removidos (D1) |
| `frontend/js/sensores.js`, `alertas.js` | Substituídos por `pontos.js` e `ocorrencias.js` |
| `backend/scripts/create_operator_sql.py` | Virou `create_operator.py` e depois `criar_operador.py` (D22), que grava no banco ou imprime o SQL (`--mostrar-sql`) |
| `backend/app/routers/__init__.py` (595 linhas, tudo junto) | Dividido em `autenticacao.py`, `pontos.py`, `medicoes.py`, `ocorrencias.py` e `auditoria.py` (em `api/app/rotas/`); as regras foram para `servicos/` |
