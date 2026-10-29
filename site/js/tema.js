// Tema claro/escuro. A primeira visita segue o sistema operacional; a escolha manual fica salva.
import { icone } from './icones.js';

const CHAVE_TEMA = 'fluvisense_tema';
const preferenciaDoSistema = window.matchMedia('(prefers-color-scheme: dark)');

function temaSalvo() {
  try {
    const valor = localStorage.getItem(CHAVE_TEMA);
    return valor === 'claro' || valor === 'escuro' ? valor : null;
  } catch {
    return null;
  }
}

export function temaAtual() {
  return document.documentElement.dataset.tema === 'escuro' ? 'escuro' : 'claro';
}

function aplicarTema(tema) {
  document.documentElement.dataset.tema = tema;
  document.querySelectorAll('[data-alternar-tema]').forEach(botao => {
    const proximo = tema === 'escuro' ? 'claro' : 'escuro';
    botao.innerHTML = icone(tema === 'escuro' ? 'sol' : 'lua') + (botao.dataset.alternarTema === 'rotulo' ? `<span>Tema ${proximo}</span>` : '');
    botao.setAttribute('aria-label', `Mudar para o tema ${proximo}`);
    botao.title = `Mudar para o tema ${proximo}`;
  });
}

export function alternarTema() {
  const proximo = temaAtual() === 'escuro' ? 'claro' : 'escuro';
  try {
    localStorage.setItem(CHAVE_TEMA, proximo);
  } catch {
    // Sem armazenamento (navegação privada): o tema vale só até fechar a página.
  }
  aplicarTema(proximo);
}

export function iniciarTema() {
  aplicarTema(temaSalvo() || (preferenciaDoSistema.matches ? 'escuro' : 'claro'));
  preferenciaDoSistema.addEventListener('change', evento => {
    if (!temaSalvo()) aplicarTema(evento.matches ? 'escuro' : 'claro');
  });
}
