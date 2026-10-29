// Aba "Simulação": gera séries de teste que nunca aparecem no mapa público.
import { api } from './api.js';
import { buscarPonto, carregarPontos, opcoesPontos } from './dados.js';
import { NOMES_VALIDADE, escaparHtml, formatarCm, formatarDataHora, graficoLinha, horarioCurto, numeroOuNulo, seloSituacao, valorCampo } from './formatacao.js';
import { avisar, blocoEstado, comBotaoOcupado, confirmarEmDialogo, focarPrimeiroErro, limparErros, marcarErro, mostrarErroFormulario } from './interface.js';

const DICAS_CENARIO = {
  subida: 'A água sobe: a distância medida diminui a partir do valor inicial.',
  descida: 'A água desce: a distância medida aumenta a partir do valor inicial.',
  oscilacao: 'A superfície oscila em torno do valor inicial (amplitude = variação ÷ 2).',
};

export async function mostrarAbaSimulacao() {
  const seletor = document.getElementById('sim-ponto');
  try {
    await carregarPontos();
  } catch (erro) {
    avisar(erro.message, 'erro');
    return;
  }
  if (seletor) {
    const atual = seletor.value;
    seletor.innerHTML = opcoesPontos(atual) || '<option value="">Nenhum ponto ativo</option>';
    if (atual) seletor.value = atual;
  }
  const temPonto = Boolean(valorCampo('sim-ponto'));
  document.querySelectorAll('#form-simulacao button').forEach(botao => { botao.disabled = !temPonto; });
  atualizarDicaCenario();
  mostrarSituacaoSimulada();
}

export function atualizarDicaCenario() {
  const dica = document.getElementById('sim-dica');
  if (dica) dica.textContent = DICAS_CENARIO[valorCampo('sim-cenario')] || '';
}

export function mostrarSituacaoSimulada() {
  const raiz = document.getElementById('sim-situacao');
  const ponto = buscarPonto(valorCampo('sim-ponto'));
  if (!raiz) return;
  if (!ponto) {
    raiz.innerHTML = blocoEstado({
      nomeIcone: 'frasco',
      titulo: 'Nenhum ponto ativo',
      texto: 'Cadastre um ponto para simular medições.',
      acao: '<button class="botao principal" type="button" onclick="mostrarAba(\'pontos\')">Ir para Rios e pontos</button>',
      compacto: true,
    });
    return;
  }
  const e = ponto.estado_simulado;
  raiz.innerHTML = `
    <div class="ponto-linha-topo"><strong>${escaparHtml(ponto.codigo)} · ${escaparHtml(ponto.nome)}</strong>${seloSituacao(e.situacao)}</div>
    <dl class="lista-detalhes" style="margin-top: var(--espaco-3)">
      <div><dt>Última simulada</dt><dd>${formatarCm(e.distancia_cm)}</dd></div>
      <div><dt>Medida em</dt><dd>${formatarDataHora(e.medida_em)}</dd></div>
      <div><dt>Validade</dt><dd>${e.validade ? NOMES_VALIDADE[e.validade] : '–'}</dd></div>
    </dl>
    <p class="texto-pequeno texto-apagado" style="margin-top: var(--espaco-2)">Critérios do ponto: atenção ≤ ${formatarCm(ponto.distancia_atencao_cm)}, alerta ≤ ${formatarCm(ponto.distancia_alerta_cm)}, crítico ≤ ${formatarCm(ponto.distancia_critica_cm)}.</p>`;
}

function lerSimulacao(formulario) {
  limparErros(formulario);
  // Campo da API: [id do campo na tela, como o campo é chamado na mensagem de erro].
  const campos = {
    distancia_inicial_cm: ['sim-inicial', 'a distância inicial'],
    variacao_cm: ['sim-variacao', 'a variação'],
    quantidade: ['sim-quantidade', 'a quantidade'],
    intervalo_minutos: ['sim-intervalo', 'o intervalo'],
  };
  const corpo = { cenario: valorCampo('sim-cenario') };
  Object.entries(campos).forEach(([campo, [id, nome]]) => {
    const valor = numeroOuNulo(valorCampo(id));
    if (valor === null || Number.isNaN(valor) || valor <= 0) marcarErro(id, `Informe ${nome} com um número maior que zero.`);
    corpo[campo] = valor;
  });
  if (corpo.quantidade && (corpo.quantidade < 2 || corpo.quantidade > 200 || !Number.isInteger(corpo.quantidade))) marcarErro('sim-quantidade', 'Use um número inteiro entre 2 e 200.');
  if (corpo.intervalo_minutos && (corpo.intervalo_minutos > 1440 || !Number.isInteger(corpo.intervalo_minutos))) marcarErro('sim-intervalo', 'Use um número inteiro entre 1 e 1.440.');
  if (corpo.cenario === 'subida' && corpo.distancia_inicial_cm && corpo.variacao_cm >= corpo.distancia_inicial_cm) {
    marcarErro('sim-variacao', 'Na subida, a variação precisa ser menor que a distância inicial.');
  }
  if (formulario.querySelector('[aria-invalid="true"]')) {
    focarPrimeiroErro(formulario);
    return null;
  }
  return corpo;
}

export async function gerarSimulacao(formulario) {
  const pontoId = valorCampo('sim-ponto');
  const corpo = lerSimulacao(formulario);
  if (!pontoId || !corpo) return;
  await comBotaoOcupado(formulario.querySelector('[type="submit"]'), async () => {
    try {
      const resultado = await api.simular(pontoId, corpo);
      const detalhe = resultado.suspeitas || resultado.invalidas ? ` (${resultado.suspeitas} suspeitas, ${resultado.invalidas} inválidas)` : '';
      avisar(`${resultado.criadas} medições simuladas criadas${detalhe}.`, 'sucesso');
      const grafico = document.getElementById('sim-grafico');
      if (grafico) {
        grafico.innerHTML = graficoLinha(resultado.medicoes.map(m => ({
          valor: m.distancia_cm,
          classe: m.validade,
          horario: horarioCurto(m.medida_em),
          rotulo: `${formatarDataHora(m.medida_em)} · ${formatarCm(m.distancia_cm)} · ${NOMES_VALIDADE[m.validade]}`,
        })), { rotulo: 'Série simulada gerada' });
      }
      await carregarPontos();
      mostrarSituacaoSimulada();
    } catch (erro) {
      mostrarErroFormulario(formulario, erro.message);
    }
  }, 'Gerando...');
}

export async function apagarSimulacao(botao) {
  const ponto = buscarPonto(valorCampo('sim-ponto'));
  if (!ponto) return;
  const confirmou = await confirmarEmDialogo({
    titulo: `Apagar medições simuladas de ${ponto.codigo}?`,
    mensagem: 'Só as medições simuladas deste ponto serão apagadas. As medições reais não são afetadas.',
    textoConfirmar: 'Apagar simuladas',
    perigo: true,
  });
  if (!confirmou) return;
  await comBotaoOcupado(botao, async () => {
    try {
      const resultado = await api.apagarSimuladas(ponto.id);
      avisar(`${resultado.apagadas} medições simuladas apagadas.`, 'sucesso');
      const grafico = document.getElementById('sim-grafico');
      if (grafico) grafico.innerHTML = '';
      await carregarPontos();
      mostrarSituacaoSimulada();
    } catch (erro) {
      avisar(erro.message, 'erro');
    }
  }, 'Apagando...');
}
