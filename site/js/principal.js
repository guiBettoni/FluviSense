// Ponto de partida do site: liga os módulos e expõe as funções usadas no HTML.
import { inserirIcones } from './icones.js';
import { alternarTema, iniciarTema } from './tema.js';
import { fecharDialogo } from './interface.js';
import { alternarMenu, focarConteudo, iniciarNavegacao, irPara, mostrarAba } from './navegacao.js';
import { entrar, sair } from './autenticacao.js';
import { aplicarFiltros, focarPonto, mostrarMapa } from './mapa.js';
import { escolherModoPainel, mostrarPainel } from './painel.js';
import {
  abrirFormularioPonto, abrirFormularioRio, copiarChaveSensor, desativarPonto, excluirPonto, excluirRio,
  gerarChaveSensor, mostrarAbaPontos, reativarPonto, salvarPonto, salvarRio,
} from './pontos.js';
import { abrirFormularioMedicao, carregarHistorico, exportarHistorico, mostrarAbaMedicoes, salvarMedicao } from './medicoes.js';
import { apagarSimulacao, atualizarDicaCenario, gerarSimulacao, mostrarSituacaoSimulada } from './simulacao.js';
import { abrirFormularioOcorrencia, encerrarOcorrencia, mostrarOcorrencias, salvarOcorrencia } from './ocorrencias.js';
import { exportarAuditoria, mostrarAuditoria } from './auditoria.js';

// Funções chamadas pelos atributos onclick/onchange/onsubmit do index.html e do HTML gerado.
// Módulos JavaScript não ficam visíveis para o HTML; por isso elas são colocadas em "window".
Object.assign(window, {
  irPara, mostrarAba, alternarMenu, focarConteudo, fecharDialogo, alternarTema,
  entrar, sair,
  aplicarFiltros, focarPonto, mostrarMapa,
  escolherModoPainel, mostrarPainel,
  abrirFormularioRio, salvarRio, excluirRio, abrirFormularioPonto, salvarPonto, desativarPonto, excluirPonto, reativarPonto,
  gerarChaveSensor, copiarChaveSensor, mostrarAbaPontos,
  carregarHistorico, exportarHistorico, abrirFormularioMedicao, salvarMedicao, mostrarAbaMedicoes,
  gerarSimulacao, apagarSimulacao, atualizarDicaCenario, mostrarSituacaoSimulada,
  mostrarOcorrencias, abrirFormularioOcorrencia, salvarOcorrencia, encerrarOcorrencia,
  exportarAuditoria, mostrarAuditoria,
});

window.addEventListener('DOMContentLoaded', () => {
  inserirIcones();
  iniciarTema();
  iniciarNavegacao();
});
