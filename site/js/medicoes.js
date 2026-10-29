// Aba "Histórico de medições": tabela, gráfico, exportação e registro manual.
import { api } from './api.js';
import { estadoTela } from './estado.js';
import { buscarPonto, carregarPontos, opcoesPontos } from './dados.js';
import {
  NOMES_ORIGEM, NOMES_SITUACAO, NOMES_VALIDADE, baixarCsv, escaparHtml, formatarCm, formatarDataHora,
  graficoLinha, horarioCurto, numeroOuNulo, seloSituacao, seloValidade, valorCampo,
} from './formatacao.js';
import {
  abrirDialogo, avisar, blocoCarregando, blocoErro, blocoEstado, campoFormulario, comBotaoOcupado,
  fecharDialogo, focarPrimeiroErro, limparErros, linhaEstado, marcarErro, mostrarErroFormulario,
} from './interface.js';

const COLUNAS = 7;
let ultimasMedicoes = [];

export async function mostrarAbaMedicoes() {
  const seletor = document.getElementById('historico-ponto');
  try {
    await carregarPontos();
  } catch (erro) {
    document.getElementById('historico-linhas').innerHTML = linhaEstado(COLUNAS, blocoErro(erro.message, 'mostrarAbaMedicoes()'));
    return;
  }
  if (seletor) {
    const atual = seletor.value;
    seletor.innerHTML = opcoesPontos(atual, { incluirInativos: true }) || '<option value="">Nenhum ponto cadastrado</option>';
    if (atual) seletor.value = atual;
  }
  await carregarHistorico();
}

export async function carregarHistorico() {
  const pontoId = valorCampo('historico-ponto');
  const modo = valorCampo('historico-modo') || 'real';
  const corpo = document.getElementById('historico-linhas');
  const grafico = document.getElementById('historico-grafico');
  if (!corpo) return;
  if (!pontoId) {
    ultimasMedicoes = [];
    corpo.innerHTML = linhaEstado(COLUNAS, blocoEstado({
      nomeIcone: 'local',
      titulo: 'Nenhum ponto cadastrado',
      texto: 'Cadastre um ponto em "Rios e pontos" para registrar medições.',
      acao: '<button class="botao principal" type="button" onclick="mostrarAba(\'pontos\')">Ir para Rios e pontos</button>',
    }));
    if (grafico) grafico.innerHTML = '';
    return;
  }
  corpo.innerHTML = linhaEstado(COLUNAS, blocoCarregando('Carregando medições...'));
  if (grafico) grafico.innerHTML = blocoCarregando('');
  try {
    ultimasMedicoes = await api.medicoes(pontoId, { modo, limite: 500 });
  } catch (erro) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoErro(erro.message, 'carregarHistorico()'));
    if (grafico) grafico.innerHTML = '';
    return;
  }
  if (!ultimasMedicoes.length) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoEstado({
      nomeIcone: 'grafico',
      titulo: 'Nenhuma medição neste filtro',
      texto: modo === 'real' ? 'Registre uma medição manual ou troque para "Simulados".' : 'Gere uma simulação na aba Simulação.',
      acao: '<button class="botao" type="button" onclick="abrirFormularioMedicao()">Registrar medição</button>',
    }));
    if (grafico) grafico.innerHTML = '<p class="texto-apagado">Sem dados para o gráfico.</p>';
    return;
  }
  corpo.innerHTML = ultimasMedicoes.map(m => `
    <tr class="${m.origem === 'simulada' ? 'linha-simulada' : ''}">
      <td data-label="Medida em" class="num">${formatarDataHora(m.medida_em)}</td>
      <td data-label="Distância" class="num"><strong>${formatarCm(m.distancia_cm)}</strong></td>
      <td data-label="Origem">${NOMES_ORIGEM[m.origem] || escaparHtml(m.origem)}</td>
      <td data-label="Validade"><span>${seloValidade(m.validade)}${m.motivo_validade ? `<span class="celula-secundaria">${escaparHtml(m.motivo_validade)}</span>` : ''}</span></td>
      <td data-label="Classificação">${m.classificacao ? seloSituacao(m.classificacao) : '–'}</td>
      <td data-label="Referência" class="num">${formatarCm(m.referencia_cm)}</td>
      <td data-label="Registrado por"><span class="texto-pequeno texto-secundario">${escaparHtml(m.registrada_por || (m.origem === 'sensor' ? 'Dispositivo' : '–'))}</span></td>
    </tr>`).join('');
  if (grafico) {
    // A API devolve da mais nova para a mais antiga; o gráfico precisa da ordem do tempo.
    const emOrdem = [...ultimasMedicoes].reverse().filter(m => m.validade !== 'invalida');
    grafico.innerHTML = graficoLinha(emOrdem.map(m => ({
      valor: m.distancia_cm,
      classe: m.validade,
      horario: horarioCurto(m.medida_em),
      rotulo: `${formatarDataHora(m.medida_em)} · ${formatarCm(m.distancia_cm)} · ${NOMES_VALIDADE[m.validade]}`,
    })), { rotulo: `Distância medida no ponto ${buscarPonto(pontoId)?.codigo || ''}` });
  }
}

export function exportarHistorico() {
  const ponto = buscarPonto(valorCampo('historico-ponto'));
  if (!ultimasMedicoes.length || !ponto) {
    avisar('Não há medições para exportar neste filtro.', 'atencao');
    return;
  }
  baixarCsv(
    `medicoes-${ponto.codigo}.csv`,
    ['Medida em', 'Distância (cm)', 'Unidade', 'Origem', 'Validade', 'Motivo', 'Classificação na época', 'Referência (cm)', 'Registrado por'],
    ultimasMedicoes.map(m => [
      m.medida_em, m.distancia_cm, m.unidade, NOMES_ORIGEM[m.origem] || m.origem, NOMES_VALIDADE[m.validade],
      m.motivo_validade || '', NOMES_SITUACAO[m.classificacao] || '', m.referencia_cm ?? '', m.registrada_por || '',
    ]),
  );
  avisar(`${ultimasMedicoes.length} medições exportadas.`, 'sucesso');
}

export function abrirFormularioMedicao() {
  if (!estadoTela.pontos.some(ponto => ponto.ativo)) {
    avisar('Cadastre um ponto ativo primeiro.', 'atencao');
    return;
  }
  abrirDialogo({
    titulo: 'Registrar medição',
    descricao: '"Manual" é uma medição real feita em campo. "Simulada" serve para testar um valor isolado, como um pico.',
    corpo: `
      <form id="form-medicao" class="form-grade" novalidate onsubmit="event.preventDefault(); salvarMedicao(this)">
        <div class="ocupa-2" data-erro-form></div>
        ${campoFormulario({ id: 'medicao-ponto', rotulo: 'Ponto', obrigatorio: true, ocupaDuas: true, controle: `<select class="selecao" id="medicao-ponto" aria-describedby="medicao-ponto-erro">${opcoesPontos(valorCampo('historico-ponto'))}</select>` })}
        ${campoFormulario({ id: 'medicao-distancia', rotulo: 'Distância sensor → água (cm)', tipo: 'number', obrigatorio: true, atributos: 'step="0.01" inputmode="decimal" autofocus' })}
        ${campoFormulario({ id: 'medicao-origem', rotulo: 'Origem', controle: '<select class="selecao" id="medicao-origem" aria-describedby="medicao-origem-erro"><option value="manual">Manual (real)</option><option value="simulada">Simulada</option></select>' })}
        ${campoFormulario({ id: 'medicao-horario', rotulo: 'Medida em', tipo: 'datetime-local', ocupaDuas: true, dica: 'Deixe vazio para usar o horário atual.' })}
      </form>`,
    rodape: `<button class="botao" type="button" data-fechar-dialogo>Cancelar</button>
      <button class="botao principal" type="submit" form="form-medicao">Registrar</button>`,
  });
}

export async function salvarMedicao(formulario) {
  limparErros(formulario);
  const distancia = numeroOuNulo(valorCampo('medicao-distancia'));
  if (distancia === null) marcarErro('medicao-distancia', 'Informe a distância em centímetros.');
  else if (Number.isNaN(distancia)) marcarErro('medicao-distancia', 'Use apenas números (ex.: 245 ou 245,5).');
  const horario = valorCampo('medicao-horario');
  // Tolerância de 5 minutos para relógios um pouco adiantados.
  if (horario && new Date(horario).getTime() > Date.now() + 5 * 60 * 1000) marcarErro('medicao-horario', 'O horário não pode estar no futuro.');
  if (formulario.querySelector('[aria-invalid="true"]')) {
    focarPrimeiroErro(formulario);
    return;
  }
  const pontoId = valorCampo('medicao-ponto');
  await comBotaoOcupado(document.querySelector('[form="form-medicao"]'), async () => {
    try {
      const resultado = await api.criarMedicao(pontoId, {
        distancia_cm: distancia,
        origem: valorCampo('medicao-origem'),
        medida_em: horario ? new Date(horario).toISOString() : null,
      });
      fecharDialogo();
      const tipo = resultado.validade === 'valida' ? 'sucesso' : 'atencao';
      avisar(`Medição registrada como ${NOMES_VALIDADE[resultado.validade].toLowerCase()}.${resultado.motivo_validade ? ` ${resultado.motivo_validade}` : ''}`, tipo);
      const seletor = document.getElementById('historico-ponto');
      if (seletor) seletor.value = pontoId;
      carregarHistorico();
    } catch (erro) {
      mostrarErroFormulario(formulario, erro.message);
    }
  }, 'Registrando...');
}
