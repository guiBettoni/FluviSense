// Navegação entre as páginas (início, mapa, login, painel) e entre as abas do painel.
import { sessao } from './api.js';
import { estadoTela } from './estado.js';
import { iniciarMapa, mostrarMapa, mostrarNumerosInicio } from './mapa.js';
import { mostrarPainel } from './painel.js';
import { mostrarAbaPontos } from './pontos.js';
import { mostrarAbaMedicoes } from './medicoes.js';
import { mostrarAbaSimulacao } from './simulacao.js';
import { mostrarOcorrencias } from './ocorrencias.js';
import { mostrarAuditoria } from './auditoria.js';
import { mostrarOperador } from './autenticacao.js';
import { avisar, fecharDialogo } from './interface.js';

const ABAS = {
  situacao: { titulo: 'Situação dos pontos', mostrar: mostrarPainel },
  pontos: { titulo: 'Rios e pontos', mostrar: mostrarAbaPontos },
  medicoes: { titulo: 'Histórico de medições', mostrar: mostrarAbaMedicoes },
  simulacao: { titulo: 'Simulação', mostrar: mostrarAbaSimulacao },
  ocorrencias: { titulo: 'Ocorrências manuais', mostrar: mostrarOcorrencias },
  auditoria: { titulo: 'Auditoria', mostrar: mostrarAuditoria },
};

const TITULOS_PAGINA = { inicio: 'Início', mapa: 'Mapa dos pontos', login: 'Área do operador', painel: 'Painel' };

// O endereço da página fica depois do "#" (ex.: index.html#mapa).
function paginaDoEndereco() {
  const pagina = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
  return TITULOS_PAGINA[pagina] ? pagina : 'inicio';
}

export function iniciarNavegacao() {
  if (!window.location.hash) window.history.replaceState(null, '', '#inicio');
  irPara(paginaDoEndereco(), { mudarEndereco: false });
  window.addEventListener('hashchange', () => irPara(paginaDoEndereco(), { mudarEndereco: false }));
  window.addEventListener('fluvisense:sessao-expirada', () => {
    avisar('Sua sessão expirou. Entre novamente.', 'atencao');
    irPara('login');
  });
  document.addEventListener('keydown', evento => {
    if (evento.key === 'Escape' && document.getElementById('moldura')?.classList.contains('nav-aberta')) alternarMenu(false);
  });
}

export function irPara(pagina, { mudarEndereco = true } = {}) {
  if (pagina === 'painel' && !sessao.ativa()) {
    avisar('Entre como operador para acessar o painel.', 'informacao');
    pagina = 'login';
    mudarEndereco = true;
  }
  if (pagina === 'login' && sessao.ativa()) pagina = 'painel';
  fecharDialogo({ forcar: true }); // ex.: a sessão expirou com um diálogo aberto
  document.querySelectorAll('.pagina').forEach(elemento => elemento.classList.remove('ativa'));
  document.getElementById(`pg-${pagina}`)?.classList.add('ativa');
  estadoTela.pagina = pagina;
  alternarMenu(false);
  if (mudarEndereco && window.location.hash !== `#${pagina}`) window.history.pushState(null, '', `#${pagina}`);
  if (pagina === 'inicio') mostrarNumerosInicio();
  if (pagina === 'mapa') {
    iniciarMapa();
    setTimeout(mostrarMapa, 60);
  }
  if (pagina === 'painel') {
    mostrarOperador();
    mostrarAba(estadoTela.aba);
  } else {
    document.title = `FluviSense | ${TITULOS_PAGINA[pagina]}`;
  }
  if (pagina === 'login') setTimeout(() => document.getElementById('login-email')?.focus(), 50);
  window.scrollTo({ top: 0, behavior: 'auto' });
}

export function mostrarAba(aba) {
  estadoTela.aba = ABAS[aba] ? aba : 'situacao';
  Object.keys(ABAS).forEach(nome => {
    document.getElementById(`aba-${nome}`)?.classList.toggle('ativa', nome === estadoTela.aba);
    const item = document.getElementById(`nav-${nome}`);
    if (!item) return;
    if (nome === estadoTela.aba) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
  const titulo = ABAS[estadoTela.aba].titulo;
  const cabecalho = document.getElementById('titulo-painel');
  if (cabecalho) cabecalho.textContent = titulo;
  document.title = `FluviSense | ${titulo}`;
  alternarMenu(false);
  ABAS[estadoTela.aba].mostrar();
}

// Gaveta de navegação no celular.
export function alternarMenu(forcar = null) {
  const moldura = document.getElementById('moldura');
  if (!moldura) return;
  const aberta = forcar === null ? !moldura.classList.contains('nav-aberta') : Boolean(forcar);
  moldura.classList.toggle('nav-aberta', aberta);
  const botao = moldura.querySelector('.botao-menu');
  botao?.setAttribute('aria-expanded', String(aberta));
  botao?.setAttribute('aria-label', aberta ? 'Fechar menu' : 'Abrir menu');
  if (aberta) moldura.querySelector('.nav-item[aria-current="page"]')?.focus();
}

// Link "Pular para o conteúdo": foca o <main> da página visível.
export function focarConteudo(evento) {
  evento?.preventDefault();
  document.querySelector('.pagina.ativa [data-principal]')?.focus();
}
