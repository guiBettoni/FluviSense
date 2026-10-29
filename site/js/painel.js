// Aba "Situação dos pontos": tabela com o estado atual de cada ponto ativo.
import { CONFIGURACAO } from './configuracao.js';
import { sessao } from './api.js';
import { estadoTela } from './estado.js';
import { carregarPontos } from './dados.js';
import { escaparHtml, formatarCm, formatarDataHora, seloSituacao, seloValidade } from './formatacao.js';
import { blocoCarregando, blocoErro, blocoEstado, linhaEstado } from './interface.js';

const COLUNAS = 7;
let atualizacao = null;
let jaCarregou = false;

// modo: 'real' (sensor e manual) ou 'simulada' (só dados de teste).
export function escolherModoPainel(modo) {
  estadoTela.modoPainel = modo === 'simulada' ? 'simulada' : 'real';
  document.querySelectorAll('[data-modo]').forEach(botao => {
    botao.setAttribute('aria-pressed', String(botao.dataset.modo === estadoTela.modoPainel));
  });
  mostrarPainel();
}

export async function mostrarPainel() {
  iniciarAtualizacao();
  const corpo = document.getElementById('painel-linhas');
  if (!corpo) return;
  if (!jaCarregou) corpo.innerHTML = linhaEstado(COLUNAS, blocoCarregando('Carregando pontos...'));
  let pontos;
  try {
    pontos = (await carregarPontos()).filter(ponto => ponto.ativo);
    jaCarregou = true;
  } catch (erro) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoErro(erro.message, 'mostrarPainel()'));
    return;
  }
  const simulado = estadoTela.modoPainel === 'simulada';
  const estados = pontos.map(ponto => (simulado ? ponto.estado_simulado : ponto.estado_real));
  const contar = condicao => estados.filter(condicao).length;
  escreverTexto('painel-pontos', pontos.length);
  escreverTexto('painel-atual', contar(e => !['sem_dados', 'desatualizado'].includes(e.situacao)));
  escreverTexto('painel-sem-atual', contar(e => ['sem_dados', 'desatualizado'].includes(e.situacao)));
  escreverTexto('painel-alerta', contar(e => ['laranja', 'vermelho'].includes(e.situacao)));
  escreverTexto('painel-suspeitas', contar(e => e.validade === 'suspeita' || e.ultima_recebida_invalida));

  const nota = document.getElementById('painel-nota-modo');
  if (nota) {
    nota.textContent = simulado
      ? 'Mostrando só dados simulados. Eles nunca aparecem no mapa público.'
      : 'Mostrando só dados reais (sensor e registro manual), com o mesmo cálculo do mapa público.';
  }

  if (!pontos.length) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoEstado({
      nomeIcone: 'local',
      titulo: 'Nenhum ponto ativo',
      texto: 'Cadastre um rio e um ponto de monitoramento para começar.',
      acao: '<button class="botao principal" type="button" onclick="mostrarAba(\'pontos\')">Ir para Rios e pontos</button>',
    }));
    return;
  }

  corpo.innerHTML = pontos.map(ponto => {
    const e = simulado ? ponto.estado_simulado : ponto.estado_real;
    const observacoes = [
      e.desatualizado ? 'Dado desatualizado' : '',
      e.ultima_recebida_invalida ? 'Última leitura inválida' : '',
      e.ocorrencia ? `Ocorrência: ${escaparHtml(e.ocorrencia.motivo)}` : '',
      ponto.distancia_atencao_cm === null ? 'Sem critérios' : (ponto.criterios_provisorios ? 'Critérios provisórios' : ''),
    ].filter(Boolean);
    return `
      <tr class="${simulado ? 'linha-simulada' : ''}">
        <td data-label="Ponto"><span><strong>${escaparHtml(ponto.codigo)}</strong><span class="celula-secundaria">${escaparHtml(ponto.nome)}</span></span></td>
        <td data-label="Rio">${escaparHtml(ponto.rio_nome || '–')}</td>
        <td data-label="Distância" class="num">${formatarCm(e.distancia_cm)}</td>
        <td data-label="Medida em" class="num">${formatarDataHora(e.medida_em)}</td>
        <td data-label="Validade">${seloValidade(e.validade) || '–'}</td>
        <td data-label="Situação">${seloSituacao(e.situacao)}</td>
        <td data-label="Observações"><span class="texto-pequeno texto-secundario">${observacoes.join(' · ') || '–'}</span></td>
      </tr>`;
  }).join('');
}

// Atualiza a tabela sozinha enquanto a aba estiver aberta.
function iniciarAtualizacao() {
  if (atualizacao) return;
  atualizacao = setInterval(() => {
    if (estadoTela.pagina === 'painel' && estadoTela.aba === 'situacao' && sessao.ativa()) mostrarPainel();
  }, CONFIGURACAO.api.intervaloAtualizacaoMs);
}

function escreverTexto(id, valor) {
  const elemento = document.getElementById(id);
  if (elemento) elemento.textContent = valor;
}
