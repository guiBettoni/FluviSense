# Requisitos

Os identificadores abaixo são da **versão 2.0** (outubro de 2026). Os requisitos de 2026.1 (RF01 a RF26, RNF01 a RNF16, RN01 a RN20) estão na [tabela de correspondência](#correspondência-com-os-requisitos-de-20261), que mostra o que foi mantido, reescrito, combinado ou retirado.

Termos usados:

- **Distância**: distância entre o sensor e a superfície da água, em centímetros. Água subindo = distância menor.
- **Fluxo real**: medições de origem `sensor` ou `manual`. **Fluxo simulado**: origem `simulada`.
- **Situação**: o que o mapa e o painel mostram para um ponto: Normal, Atenção, Alerta, Crítico, Sem critério, Desatualizado ou Sem dados.

## Requisitos funcionais

| ID | Requisito | Critérios de aceitação | Teste automatizado |
|---|---|---|---|
| RF01 | O operador cadastra, edita, lista e exclui rios. | Nome obrigatório e único, sem diferenciar maiúsculas. Qualquer pessoa pode listar. Só é possível excluir um rio sem nenhum ponto ligado (ativo ou desativado); a exclusão pede confirmação e fica na auditoria. | `test_pontos.py::test_rios`, `test_exclusoes.py` |
| RF02 | O operador cadastra, edita, desativa, reativa e exclui pontos de monitoramento. | Código único (letras, números, `-` e `_`, gravado em maiúsculas). Rio, nome, latitude e longitude obrigatórios. Desativar não apaga histórico e tira o ponto do mapa. Ponto desativado não recebe medições. Excluir só é possível para ponto sem medição real e sem ocorrência; as medições simuladas dele são apagadas junto. Ponto com histórico real só pode ser desativado. A exclusão pede confirmação e fica na auditoria. | `test_pontos.py::test_codigo_duplicado_e_rio_inexistente`, `::test_desativar_ponto_mantem_historico_e_tira_do_mapa`, `test_exclusoes.py` |
| RF03 | Cada ponto tem seus próprios critérios de classificação: distâncias de atenção, alerta e crítico, indicação de provisório e justificativa. | Os três valores preenchidos (atenção > alerta > crítico > 0) ou os três vazios. Novo ponto nasce com critérios provisórios. Alterações vão para a auditoria com valor anterior e novo. | `test_pontos.py::test_criterios_precisam_ser_completos_e_ordenados`, `::test_alteracao_de_criterios_fica_na_auditoria_com_antes_e_depois` |
| RF04 | Cada ponto tem parâmetros de validação próprios: distância mínima e máxima válidas, salto máximo entre leituras e prazo para ficar desatualizado. | Mínima < máxima. Prazo entre 1 e 43.200 min (padrão 720 min = 12 h). Parâmetros de um ponto não afetam outro. | `test_pontos.py::test_varios_pontos_com_configuracao_propria`, `test_medicoes.py::test_limite_de_salto_configurado_no_ponto` |
| RF05 | O sistema registra medições com valor, unidade, horário, ponto e origem: manual pelo operador ou por sensor com chave do ponto. | Unidade sempre `cm`. Sem horário informado, vale o de recebimento. Horário mais de 5 min no futuro é recusado. O valor recebido é sempre guardado, mesmo quando inválido. | `test_medicoes.py::test_medicao_guarda_valor_unidade_horario_ponto_e_origem`, `::test_horario_no_futuro_e_rejeitado`, `test_sensor_e_auditoria.py::test_dispositivo_precisa_da_chave_do_proprio_ponto` |
| RF06 | O operador gera séries simuladas de subida, descida e oscilação, registra medições simuladas avulsas e apaga as simuladas de um ponto. | Subida: distância cai do valor inicial até inicial − variação. Descida: sobe até inicial + variação. Oscilação: um ciclo em torno do inicial, com amplitude variação/2. Série que chegaria a distância ≤ 0 é recusada. Apagar atinge só medições simuladas. | `test_simulacao_e_situacao.py` (testes de subida, descida, oscilação e limpeza) |
| RF07 | O operador consulta o histórico de um ponto, filtrando por fluxo (real, simulado ou todos) e por período, com gráfico e exportação em CSV. | Ordem do mais recente para o mais antigo. Cada linha mostra validade, motivo, classificação na época e referência usada. | `test_medicoes.py::test_historico_ordenado_e_filtrado_por_modo` |
| RF08 | O mapa público mostra os pontos ativos com a situação calculada **só com dados reais**, com filtros por rio e por situação. | Não mostra dados simulados nem configuração interna (chave, limites técnicos). Indica dado desatualizado, leitura suspeita, ocorrência aberta e critério provisório. | `test_pontos.py::test_rota_publica_nao_expoe_configuracao_interna`, `test_simulacao_e_situacao.py::test_simulacao_nao_contamina_dados_reais_nem_o_mapa` |
| RF09 | O painel do operador mostra a situação de todos os pontos ativos e alterna entre dados reais e simulados. | Indicadores: pontos ativos, com dado atual, em alerta ou crítico, sem dado atual, leituras suspeitas ou inválidas. | Teste de fumaça da interface ([validação](05-validacao.md)) |
| RF10 | O operador registra uma ocorrência manual num ponto (Atenção, Alerta ou Crítico, com motivo) e depois a encerra. | No máximo uma ocorrência aberta por ponto. Enquanto aberta, define a situação real do ponto. Ao encerrar, a situação volta a ser calculada pelas medições. | `test_simulacao_e_situacao.py::test_ocorrencia_manual_prevalece_e_ao_encerrar_volta_ao_calculo` |
| RF11 | O sistema registra na auditoria as alterações importantes e permite consultá-las e exportá-las. | Registra: login; criação, alteração e exclusão de rios; criação, alteração, desativação e exclusão de pontos; critérios; chave do sensor; medição manual; simulação e limpeza; ocorrências. Guarda quem fez e quando. | `test_sensor_e_auditoria.py::test_auditoria_registra_alteracoes_sem_guardar_segredos` |
| RF12 | O operador entra com e-mail e senha. | Senha errada é recusada. A sessão expira (padrão 8 h). | `test_autenticacao.py::test_login_correto_e_incorreto` |

## Requisitos não funcionais

| ID | Requisito | Como é verificado |
|---|---|---|
| RNF01 | **Acesso protegido.** Toda operação de escrita exige token de operador. A única exceção é o envio por sensor, que exige a chave do próprio ponto. Senhas e chaves são guardadas só como hash. Segredos ficam em variáveis de ambiente, nunca no código, e a API não liga sem um segredo de pelo menos 32 caracteres. O login bloqueia por 15 minutos depois de 5 senhas erradas seguidas. As tabelas têm RLS ligada, para a API automática do Supabase não expor dados. HTTPS é feito pela hospedagem. | `test_autenticacao.py` (17 rotas testadas sem token), `test_seguranca.py`, `test_sensor_e_auditoria.py` |
| RNF02 | **Separação real × simulado.** Medições simuladas não aparecem no mapa público, não mudam a situação real e não entram na referência das medições reais. | `test_simulacao_e_situacao.py::test_simulacao_nao_contamina_dados_reais_nem_o_mapa` |
| RNF03 | **Transparência dos dados.** Leituras inválidas, suspeitas e dados desatualizados são identificados na interface e na API. Critério provisório também. | Testes de RN04 a RN06 |
| RNF04 | **Histórico preservado.** A API não apaga medições reais nem ocorrências. Um ponto com esse histórico só pode ser desativado, e um rio com pontos não pode ser excluído. Só medições simuladas, pontos sem histórico real e rios vazios podem ser apagados. | `test_desativar_ponto_mantem_historico_e_tira_do_mapa`, `test_limpar_simulacao_apaga_so_simuladas`, `test_exclusoes.py` |
| RNF05 | **Reprodutível.** O banco é criado só pelas migrações versionadas (`scripts/migrar.py`), sem passos manuais escondidos. O README descreve instalação, execução e testes. As dependências têm versão fixa. | `test_migracoes.py` (em PostgreSQL) |
| RNF06 | **Responsivo e em português.** Mapa e lista de pontos são usáveis num celular de 390 px de largura, sem rolagem horizontal. As mensagens de erro, inclusive as de validação geradas pela API, aparecem em português. | Teste de fumaça da interface, `test_mensagens.py` |
| RNF07 | **Privacidade.** O sistema não guarda dados pessoais além do nome e do e-mail do operador. A auditoria não guarda senhas nem chaves. | `test_auditoria_registra_alteracoes_sem_guardar_segredos` |
| RNF08 | **Comunicação honesta.** A interface não afirma prever enchentes nem emitir alertas oficiais. Informa que o sistema é complementar e mostra os telefones 199 e 193. | Revisão da interface (`index.html`) |

## Regras de negócio

| ID | Regra |
|---|---|
| RN01 | A grandeza registrada é a distância sensor → superfície da água, em cm. O sistema não calcula nível absoluto, porque isso exigiria a cota de instalação de cada sensor. |
| RN02 | Classificação de uma medição: distância ≤ crítico → **Crítico**; ≤ alerta → **Alerta**; ≤ atenção → **Atenção**; acima disso → **Normal**. Ponto sem critérios → **Sem critério**. |
| RN03 | Critérios novos nascem como **provisórios**. O operador só deve desmarcar quando houver uma referência, que fica registrada na justificativa. |
| RN04 | **Medição inválida**: distância ≤ 0, abaixo da mínima ou acima da máxima configurada. É guardada com o motivo, mas não muda a situação do ponto nem entra na referência. |
| RN05 | **Medição suspeita**: a diferença em relação à referência passa do limite. A referência é a mediana das 3 últimas medições não inválidas do mesmo fluxo; o limite é `max_jump_cm` do ponto ou, se vazio, 50% da referência. A medição suspeita é guardada, **é exibida com aviso** e entra na referência. Assim, um pico isolado não muda a referência, e uma mudança real que se mantém vira referência na 3ª leitura. Com menos de 3 medições anteriores, a medição é válida. |
| RN06 | **Dado desatualizado**: se a última medição aproveitável tem mais tempo que o prazo do ponto, a situação exibida é **Desatualizado**. A classificação antiga aparece só como informação, nunca como condição atual. Sem nenhuma medição aproveitável: **Sem dados**. |
| RN07 | Os fluxos real e simulado são independentes: cada um tem sua própria referência e sua própria situação. |
| RN08 | Uma ocorrência manual aberta define a situação real do ponto até ser encerrada. Só pode haver uma aberta por ponto. |
| RN09 | Uma chave de sensor só vale para o ponto em que foi gerada. Gerar uma nova chave invalida a anterior. |
| RN10 | O horário da medição é o informado pelo sensor ou pelo operador (no máximo 5 min no futuro). Sem horário, vale o de recebimento. Medições enviadas com atraso entram no histórico na posição do horário em que foram medidas. |

## Correspondência com os requisitos de 2026.1

Fonte: `Documento de Requisitos.pdf` e AV2 de junho de 2026 (os dois têm o mesmo texto; a AV2 corrige a RN14).

Legenda: **Mantido** (mesmo sentido), **Reescrito** (mesma necessidade, regra nova), **Combinado** (absorvido por outro item), **Retirado** (saiu do escopo do sistema).

### Requisitos funcionais antigos

| Antigo | Assunto | Decisão | Novo / motivo |
|---|---|---|---|
| RF01 | Coleta e armazenamento de leituras | Reescrito | RF05. Sem conversão distância→nível (falta referência de instalação) |
| RF02 | APIs Epagri/Cemaden | Retirado | Fora do objetivo do sistema |
| RF03 | Cruzamento com pontos históricos | Retirado | Depende do RF02 antigo |
| RF04 | Cadastro de morador | Retirado | Sem notificações, os dados pessoais não teriam finalidade (LGPD) |
| RF05 | Endereços adicionais | Retirado | Depende do RF04 antigo |
| RF06 | Mapa público | Reescrito | RF08. Sem abrigos; só dados reais |
| RF07 | Verificação por WhatsApp | Retirado | O sistema não envia notificações |
| RF08 | Respostas por WhatsApp | Retirado | Idem |
| RF09 | Mensagem de retração | Retirado | Idem |
| RF10 | Painel do operador | Reescrito | RF09 |
| RF11 | Ocorrência manual | Reescrito | RF10. Classificação escolhida e encerramento |
| RF12 | Abrigos | Retirado | Não faz parte do monitoramento dos rios |
| RF13 | Auditoria | Mantido | RF11 |
| RF14 | Exportação CSV/PDF | Combinado | RF07 (CSV do histórico) e RF11 (CSV da auditoria). PDF removido |
| RF15 | Modo de simulação | Reescrito | RF06 e RNF02 |
| RF16 | Autenticação | Reescrito | RF12. Só operador |
| RF17 | Dispositivos ESP32 | Combinado | RF02 (ponto e sensor juntos) e RN09 (chave) |
| RF18 | Limiares por ponto | Reescrito | RF03. Em distância, provisórios |
| RF19 | Gerenciar moradores | Retirado | Depende do RF04 antigo |
| RF20 | Envio de alerta | Retirado | O sistema não emite alertas; mostra classificação (RF08, RF09) |
| RF21 | Pedido de ajuda | Retirado | Fora do objetivo do sistema |
| RF22 | Triagem de pedidos | Retirado | Idem |
| RF23 | Pedido sem conexão | Retirado | Idem |
| RF24 | Envio posterior de pedidos | Retirado | Idem |
| RF25 | Solicitação de alerta público | Retirado | Alerta oficial é atribuição da Defesa Civil |
| RF26 | Contatos oficiais | Combinado | RNF08 (aviso com 199 e 193) |

### Requisitos não funcionais antigos

| Antigo | Assunto | Decisão | Novo / motivo |
|---|---|---|---|
| RNF01 | LGPD | Reescrito | RNF07 |
| RNF02 | Prioridade em desastre | Retirado | Não há fila de notificações |
| RNF03 | Disponibilidade 99% | Retirado | Depende da hospedagem; não verificável no projeto |
| RNF04 | HTTPS | Combinado | RNF01 |
| RNF05 | Controle de acesso | Combinado | RNF01 |
| RNF06 | Interface responsiva | Mantido | RNF06 |
| RNF07 | Confirmar alagamento em 3 interações | Retirado | Dependia de moradores e WhatsApp |
| RNF08 | Tolerância a falhas do sensor | Reescrito | RN04 e RN05. A regra antiga travava o ponto depois de um salto real (ver [decisões](04-decisoes.md#d6)) |
| RNF09 | Vários dispositivos | Combinado | RF02 |
| RNF10 | Manutenibilidade | Reescrito | RNF05 |
| RNF11 | Tempo de resposta | Retirado | Não há meta de desempenho definida |
| RNF12 | Recuperação de falhas | Retirado (parcial) | RN10 aceita medição enviada com atraso; o armazenamento no dispositivo é responsabilidade do sensor |
| RNF13 | Funcionamento offline | Retirado | Fora do objetivo do sistema |
| RNF14 | Linguagem clara | Combinado | RNF08 |
| RNF15 | Rastreabilidade | Combinado | RF11 |
| RNF16 | Resiliência operacional | Retirado | Fora do objetivo do sistema |

### Regras de negócio antigas

| Antigo | Assunto | Decisão | Novo / motivo |
|---|---|---|---|
| RN01 | Situação = sensor + moradores | Reescrito | RN02 e RN08 (medições e ocorrência manual) |
| RN02 | Pesos do sensor e 3 confirmações | Retirado | Não há confirmações de moradores |
| RN03 | Sensor só atualiza o próprio ponto | Mantido | RN09 |
| RN04 | Bloqueio por respostas NÃO | Retirado | Depende do WhatsApp |
| RN05 | Validade de 12 h | Reescrito | RN06 (prazo por ponto, padrão 12 h) |
| RN06 | Escalonamento sem pular etapas | Retirado | A classificação é direta pela distância; não há disparo de alertas |
| RN07 | Histórico não pode ser apagado | Reescrito | RNF04. O prazo de 2 anos não é automatizado; nada é apagado |
| RN08 | Mensagens por bairro | Retirado | Depende de notificações |
| RN09 | Uma resposta por hora | Retirado | Idem |
| RN10 | Janela de 30 min para resposta | Retirado | Idem |
| RN11 | Escalonamento automático | Retirado | O sistema não escala alertas |
| RN12 | Encerramento automático de alerta | Retirado | A situação acompanha a última medição; não há alerta com ciclo de vida |
| RN13 | Pontos relevantes por endereço | Retirado | Depende do cadastro de moradores |
| RN14 | Simulação isolada | Mantido | RN07 e RNF02 (a citação errada do RF19 foi corrigida) |
| RN15 | Subida contínua em 3 leituras | Retirado | Regra sem validação em campo; a suspeita de salto (RN05) cobre variações bruscas |
| RN16 | Sistema complementar | Mantido | RNF08 |
| RN17 a RN20 | Regras dos pedidos de ajuda | Retirado | O sistema não trata pedidos de ajuda |
