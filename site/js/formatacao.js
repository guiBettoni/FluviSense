// Funções de exibição usadas por todas as telas.

export const NOMES_SITUACAO = {
  verde: 'Normal',
  amarelo: 'Atenção',
  laranja: 'Alerta',
  vermelho: 'Crítico',
  sem_criterio: 'Sem critério',
  desatualizado: 'Desatualizado',
  sem_dados: 'Sem dados',
};

export const NOMES_VALIDADE = {
  valida: 'Válida',
  suspeita: 'Suspeita',
  invalida: 'Inválida',
};

export const NOMES_ORIGEM = {
  sensor: 'Sensor',
  manual: 'Manual',
  simulada: 'Simulada',
};

export function plural(quantidade, singular, formaPlural) {
  return `${quantidade} ${quantidade === 1 ? singular : formaPlural}`;
}

// Troca os caracteres especiais do HTML, para que um texto digitado nunca vire código na página.
export function escaparHtml(texto) {
  return String(texto ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function seloSituacao(situacao) {
  const chave = situacao || 'sem_dados';
  return `<span class="selo ${chave}">${NOMES_SITUACAO[chave] || escaparHtml(chave)}</span>`;
}

export function seloValidade(validade) {
  if (!validade) return '';
  return `<span class="selo ${validade}">${NOMES_VALIDADE[validade] || escaparHtml(validade)}</span>`;
}

export function formatarDataHora(valor) {
  if (!valor) return '–';
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return '–';
  return data.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function formatarCm(valor) {
  if (valor === null || valor === undefined || valor === '') return '–';
  return `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 2 })} cm`;
}

export function numeroOuNulo(valor) {
  if (valor === null || valor === undefined || String(valor).trim() === '') return null;
  const numero = Number(String(valor).replace(',', '.'));
  return Number.isFinite(numero) ? numero : NaN;
}

export function valorCampo(id) {
  return document.getElementById(id)?.value.trim() ?? '';
}

export function baixarCsv(nomeArquivo, cabecalho, linhas) {
  const celula = valor => `"${String(valor ?? '').replaceAll('"', '""')}"`;
  const csv = [cabecalho, ...linhas].map(linha => linha.map(celula).join(';')).join('\n');
  const endereco = URL.createObjectURL(new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a');
  link.href = endereco;
  link.download = nomeArquivo;
  link.click();
  URL.revokeObjectURL(endereco);
}

// Gráfico de linha em SVG. Eixo vertical: distância (cm); eixo horizontal: horário da medição.
// As cores vêm das variáveis do tema (classes .grafico em componentes.css).
export function graficoLinha(pontos, { altura = 220, rotulo = 'Gráfico da distância medida' } = {}) {
  if (pontos.length < 2) {
    return '<p class="texto-apagado">São necessárias pelo menos duas medições para desenhar o gráfico.</p>';
  }
  const largura = 720;
  const margem = { cima: 16, direita: 16, baixo: 28, esquerda: 64 };
  const valores = pontos.map(ponto => ponto.valor);
  let minimo = Math.min(...valores);
  let maximo = Math.max(...valores);
  if (minimo === maximo) { minimo -= 1; maximo += 1; }
  const x = indice => margem.esquerda + (indice * (largura - margem.esquerda - margem.direita)) / (pontos.length - 1);
  const y = valor => margem.cima + ((maximo - valor) * (altura - margem.cima - margem.baixo)) / (maximo - minimo);
  const marcas = [maximo, (maximo + minimo) / 2, minimo];
  const grade = marcas.map(valor => `
    <line class="linha-grade" x1="${margem.esquerda}" x2="${largura - margem.direita}" y1="${y(valor).toFixed(1)}" y2="${y(valor).toFixed(1)}" />
    <text class="rotulo-eixo" x="${margem.esquerda - 8}" y="${(y(valor) + 4).toFixed(1)}" text-anchor="end">${formatarCm(valor)}</text>`).join('');
  const linha = pontos.map((ponto, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(ponto.valor).toFixed(1)}`).join(' ');
  const area = `${linha} L${x(pontos.length - 1).toFixed(1)},${altura - margem.baixo} L${x(0).toFixed(1)},${altura - margem.baixo} Z`;
  const bolinhas = pontos.map((ponto, i) => `<circle class="bolinha-grafico ${ponto.classe || ''}" cx="${x(i).toFixed(1)}" cy="${y(ponto.valor).toFixed(1)}" r="${pontos.length > 60 ? 2.5 : 4}"><title>${escaparHtml(ponto.rotulo || '')}</title></circle>`).join('');
  const rotuloHorario = (ponto, ancora, i) => ponto.horario ? `<text class="rotulo-eixo" x="${x(i).toFixed(1)}" y="${altura - 8}" text-anchor="${ancora}">${escaparHtml(ponto.horario)}</text>` : '';
  const temSuspeita = pontos.some(ponto => ponto.classe === 'suspeita');
  return `
    <svg class="grafico" viewBox="0 0 ${largura} ${altura}" role="img" aria-label="${escaparHtml(rotulo)}">
      ${grade}
      <path class="area" d="${area}" />
      <path class="linha" d="${linha}" />
      ${bolinhas}
      ${rotuloHorario(pontos[0], 'start', 0)}
      ${rotuloHorario(pontos[pontos.length - 1], 'end', pontos.length - 1)}
    </svg>
    <div class="grafico-legenda"><span><i></i>Válida</span>${temSuspeita ? '<span><i class="suspeita"></i>Suspeita</span>' : ''}<span>${pontos.length} medições</span></div>`;
}

export function horarioCurto(valor) {
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return '';
  return data.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
