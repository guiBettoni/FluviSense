# Visão e escopo

## Problema

Palhoça tem bairros que alagam com frequência quando os rios sobem. Os órgãos de monitoramento hidrológico, como Epagri/Ciram, Cemaden e Defesa Civil, trabalham com estações em pontos selecionados de cada bacia. Isso resulta em poucos pontos por município: na consulta feita pelo autor aos portais públicos desses órgãos em outubro de 2026, foi encontrado um único ponto de leitura de rio divulgado para Palhoça.

Um ponto só não mostra o que acontece em trechos menores, como canais e afluentes perto de áreas que costumam alagar.

## Proposta

O FluviSense monta uma rede de **micropontos de leitura**. Em cada ponto, um sensor ultrassônico barato, instalado acima da água (numa ponte ou num poste na margem), mede a distância até a superfície do rio. O sistema:

- guarda as medições;
- confere se cada leitura é válida;
- mostra a situação de todos os pontos num mapa.

O FluviSense não substitui os órgãos oficiais. Ele amplia a quantidade de pontos acompanhados e pode servir de apoio a quem já faz esse monitoramento.

## Objetivo

Registrar e acompanhar, ponto a ponto, a distância entre o sensor e a superfície da água em rios de Palhoça, com dados confiáveis, histórico consultável e uma visualização clara da situação de cada ponto.

## O que o sistema faz

- Cadastro de **rios** e de **pontos de monitoramento**. Cada ponto tem rio, localização e configuração própria.
- **Critérios de classificação** por ponto: três distâncias (atenção, alerta e crítico), definidas pelo operador. Elas ficam marcadas como provisórias enquanto não houver uma referência que as confirme.
- **Validação de cada leitura:**
  - **inválida**: leitura impossível, como distância zero ou fora da faixa do sensor;
  - **suspeita**: salto brusco em relação às leituras anteriores;
  - **desatualizada**: dado antigo demais para representar o momento.
- **Registro de medições** com valor, unidade (cm), horário, ponto e origem. A origem pode ser sensor (com chave por ponto), manual (feita em campo pelo operador) ou simulada.
- **Simulação** de subida, descida e oscilação da água, separada dos dados reais, para testar a configuração de um ponto.
- **Histórico** por ponto, com gráfico e exportação em CSV.
- **Mapa público** só com dados reais, com filtros por rio e por situação.
- **Painel do operador** com a situação de todos os pontos.
- **Ocorrência manual**: o operador registra uma observação de campo que prevalece sobre as medições até ser encerrada.
- **Auditoria** das alterações importantes.

## Decisões que delimitam o sistema

- A grandeza medida é a **distância** sensor → água. O sistema não calcula o nível absoluto do rio, porque isso exigiria a cota de instalação de cada sensor, que não está definida.
- O sistema não traz limiares oficiais. Os critérios de cada ponto são do operador e aparecem como provisórios.
- Há **um operador** por vez (regra da migração 002).
- O mapa usa Leaflet e OpenStreetMap, carregados pela internet. Sem eles, a lista de pontos continua funcionando.
