// Mapa público (Leaflet) e números da página inicial.
// "L" é o nome global que a biblioteca Leaflet cria; não dá para traduzir.
import { CONFIGURACAO } from './configuracao.js';
import { api } from './api.js';
import { estadoTela } from './estado.js';
import { NOMES_SITUACAO, escaparHtml, formatarCm, formatarDataHora, seloSituacao } from './formatacao.js';
import { blocoCarregando, blocoErro, blocoEstado } from './interface.js';

let mapa = null;
let marcadores = new Map();
let atualizacao = null;
let pontosCarregados = [];
let erroCarregamento = '';
let jaCarregou = false;

export function iniciarMapa() {
  if (!atualizacao) {
    atualizacao = setInterval(() => {
      if (estadoTela.pagina === 'mapa') mostrarMapa();
    }, CONFIGURACAO.api.intervaloAtualizacaoMs);
  }
  if (mapa || typeof L === 'undefined') return;
  mapa = L.map('mapa', { zoomControl: true }).setView(CONFIGURACAO.centro, CONFIGURACAO.aproximacao);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; colaboradores do OpenStreetMap',
    maxZoom: 19,
  }).addTo(mapa);
}

export async function mostrarMapa() {
  const lista = document.getElementById('mapa-pontos');
  if (!jaCarregou && lista) lista.innerHTML = blocoCarregando('Carregando pontos...');
  try {
    const [pontos, rios] = await Promise.all([api.pontosPublicos(), api.rios()]);
    pontosCarregados = pontos;
    erroCarregamento = '';
    jaCarregou = true;
    preencherFiltroRios(rios);
  } catch (erro) {
    erroCarregamento = erro.message;
  }
  desenharMapa();
}

function preencherFiltroRios(rios) {
  const seletor = document.getElementById('mapa-rio');
  if (!seletor) return;
  const atual = seletor.value;
  seletor.innerHTML = '<option value="">Todos os rios</option>'
    + rios.map(rio => `<option value="${escaparHtml(rio.nome)}">${escaparHtml(rio.nome)}</option>`).join('');
  seletor.value = atual;
}

function pontosVisiveis() {
  const rio = document.getElementById('mapa-rio')?.value || '';
  const situacao = document.getElementById('mapa-situacao')?.value || '';
  return pontosCarregados.filter(ponto => {
    if (rio && ponto.rio_nome !== rio) return false;
    if (situacao && ponto.estado.situacao !== situacao) return false;
    return true;
  });
}

export function aplicarFiltros() {
  desenharMapa();
}

// Linhas de explicação da situação do ponto (usadas na lista e no balão do mapa).
function explicacoes(ponto) {
  const e = ponto.estado;
  const linhas = e.distancia_cm === null
    ? ['Nenhuma medição real recebida.']
    : [`Distância sensor → água: <strong>${formatarCm(e.distancia_cm)}</strong>`, `Medida em ${formatarDataHora(e.medida_em)}`];
  if (e.desatualizado) linhas.push('<span class="alerta-texto">Dado desatualizado: não representa a condição atual.</span>');
  if (e.validade === 'suspeita') linhas.push('<span class="alerta-texto">Leitura suspeita (variação brusca), aguardando confirmação.</span>');
  if (e.ocorrencia) linhas.push(`<span class="alerta-texto">Ocorrência registrada pelo operador: ${escaparHtml(e.ocorrencia.motivo)}</span>`);
  if (!ponto.possui_criterios) linhas.push('Ponto sem critérios de classificação.');
  else if (ponto.criterios_provisorios) linhas.push('Critérios provisórios, sem referência hidrológica validada.');
  return linhas;
}

export function focarPonto(id) {
  const marcador = marcadores.get(Number(id));
  if (!marcador || !mapa) return;
  mapa.flyTo(marcador.getLatLng(), Math.max(mapa.getZoom(), 14), { duration: 0.6 });
  marcador.openPopup();
  if (window.matchMedia('(max-width: 1024px)').matches) document.getElementById('mapa')?.scrollIntoView({ behavior: 'smooth' });
}

function desenharMapa() {
  const pontos = pontosVisiveis();
  const lista = document.getElementById('mapa-pontos');
  if (lista) {
    if (erroCarregamento && !pontosCarregados.length) {
      lista.innerHTML = blocoErro(erroCarregamento, 'mostrarMapa()');
    } else if (!pontos.length) {
      lista.innerHTML = blocoEstado({
        nomeIcone: 'local',
        titulo: pontosCarregados.length ? 'Nenhum ponto neste filtro' : 'Nenhum ponto cadastrado',
        texto: pontosCarregados.length ? 'Mude o rio ou a situação para ver outros pontos.' : 'Os pontos aparecem aqui assim que o operador cadastrar.',
        compacto: true,
      });
    } else {
      lista.innerHTML = pontos.map(ponto => `
        <button class="ponto-linha" type="button" onclick="focarPonto(${ponto.id})" ${mapa ? '' : 'disabled'}>
          <span class="ponto-linha-topo"><strong>${escaparHtml(ponto.nome)}</strong>${seloSituacao(ponto.estado.situacao)}</span>
          <span class="texto-pequeno texto-apagado">${escaparHtml(ponto.rio_nome || 'Rio não informado')}${ponto.bairro ? ` · ${escaparHtml(ponto.bairro)}` : ''}</span>
          <span class="observacoes">${explicacoes(ponto).map(linha => `<span>${linha}</span>`).join('')}</span>
        </button>`).join('');
    }
  }
  if (!mapa) {
    const tela = document.getElementById('mapa');
    if (tela && !tela.querySelector('.mapa-aviso')) {
      tela.innerHTML = `<div class="mapa-aviso">${blocoEstado({ nomeIcone: 'mapa', titulo: 'Mapa indisponível', texto: 'A biblioteca de mapas não carregou (verifique a internet). A lista de pontos continua disponível.' })}</div>`;
    }
    return;
  }
  marcadores.forEach(marcador => marcador.remove());
  marcadores = new Map();
  pontos.forEach(ponto => {
    const situacao = ponto.estado.situacao;
    const desenho = L.divIcon({
      className: '',
      html: `<div class="mapa-marcador ${situacao}"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });
    const marcador = L.marker([ponto.latitude, ponto.longitude], { icon: desenho, title: `${ponto.nome}: ${NOMES_SITUACAO[situacao]}`, keyboard: true })
      .addTo(mapa)
      .bindPopup(`<strong>${escaparHtml(ponto.nome)}</strong> <span class="texto-apagado">(${escaparHtml(ponto.codigo)})</span><br>${seloSituacao(situacao)}<br>${explicacoes(ponto).join('<br>')}`);
    marcadores.set(ponto.id, marcador);
  });
  mapa.invalidateSize();
}

// Números da página inicial, calculados com os mesmos dados públicos do mapa.
export async function mostrarNumerosInicio() {
  try {
    const pontos = await api.pontosPublicos();
    const comDadoAtual = pontos.filter(p => !['sem_dados', 'desatualizado'].includes(p.estado.situacao)).length;
    const escrever = (id, valor) => { const elemento = document.getElementById(id); if (elemento) elemento.textContent = valor; };
    escrever('inicio-pontos', pontos.length);
    escrever('inicio-atual', comDadoAtual);
    escrever('inicio-sem-atual', pontos.length - comDadoAtual);
    escrever('inicio-rios', new Set(pontos.map(p => p.rio_nome).filter(Boolean)).size);
  } catch {
    // Sem API, a página inicial continua funcionando e os números ficam em "–".
  }
}
