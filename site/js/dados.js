// Listas de pontos e rios usadas por várias abas do painel.
import { api } from './api.js';
import { estadoTela } from './estado.js';
import { escaparHtml } from './formatacao.js';

export async function carregarPontos() {
  estadoTela.pontos = await api.pontos();
  return estadoTela.pontos;
}

export async function carregarRios() {
  estadoTela.rios = await api.rios();
  return estadoTela.rios;
}

export function buscarPonto(id) {
  return estadoTela.pontos.find(ponto => ponto.id === Number(id)) || null;
}

// <option> dos pontos ativos para os seletores do painel.
export function opcoesPontos(selecionadoId = null, { incluirInativos = false } = {}) {
  return estadoTela.pontos
    .filter(ponto => incluirInativos || ponto.ativo)
    .map(ponto => `<option value="${ponto.id}" ${ponto.id === Number(selecionadoId) ? 'selected' : ''}>${escaparHtml(ponto.codigo)} · ${escaparHtml(ponto.nome)}</option>`)
    .join('');
}

export function opcoesRios(selecionadoId = null) {
  return estadoTela.rios
    .map(rio => `<option value="${rio.id}" ${rio.id === Number(selecionadoId) ? 'selected' : ''}>${escaparHtml(rio.nome)}</option>`)
    .join('');
}
