// Ícones de contorno no estilo Fluent (grade 20x20, traço de 1,5 px, cantos arredondados).
// Uso no HTML: <span data-icone="nome"></span>. Uso no JS: icone('nome').

const desenhos = {
  inicio: '<path d="M3.5 8.5 10 3l6.5 5.5V16a1 1 0 0 1-1 1h-3.5v-5h-4v5H4.5a1 1 0 0 1-1-1V8.5Z"/>',
  mapa: '<path d="M7.5 3.5 3 5.2v11.3l4.5-1.7 5 1.7 4.5-1.7V3.5l-4.5 1.7-5-1.7Z"/><path d="M7.5 3.5v11.3M12.5 5.2v11.3"/>',
  local: '<path d="M10 17.5s5.5-4.6 5.5-9.5a5.5 5.5 0 0 0-11 0c0 4.9 5.5 9.5 5.5 9.5Z"/><circle cx="10" cy="8" r="2"/>',
  entrar: '<path d="M11 3.5h3.5a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H11"/><path d="M3.5 10h8M8.5 6.5 12 10l-3.5 3.5"/>',
  sair: '<path d="M9 3.5H5.5a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1H9"/><path d="M8 10h8.5M13.5 6.5 17 10l-3.5 3.5"/>',
  sol: '<circle cx="10" cy="10" r="3.25"/><path d="M10 2.5v1.5M10 16v1.5M2.5 10H4M16 10h1.5M4.7 4.7l1 1M14.3 14.3l1 1M4.7 15.3l1-1M14.3 5.7l1-1"/>',
  lua: '<path d="M16.5 12.2A6.75 6.75 0 0 1 7.8 3.5a6.75 6.75 0 1 0 8.7 8.7Z"/>',
  menu: '<path d="M3.5 5.5h13M3.5 10h13M3.5 14.5h13"/>',
  grade: '<rect x="3.5" y="3.5" width="5.5" height="5.5" rx="1"/><rect x="11" y="3.5" width="5.5" height="5.5" rx="1"/><rect x="3.5" y="11" width="5.5" height="5.5" rx="1"/><rect x="11" y="11" width="5.5" height="5.5" rx="1"/>',
  agua: '<path d="M10 3c2.8 3.6 5 6.3 5 9a5 5 0 0 1-10 0c0-2.7 2.2-5.4 5-9Z"/><path d="M7.5 12.5a2.5 2.5 0 0 0 2.5 2.2"/>',
  grafico: '<path d="M3.5 3.5v13h13"/><path d="m6.5 12.5 3-3.5 2.5 2 4-5"/>',
  frasco: '<path d="M7.5 3.5h5M8.5 3.5v4.2L4.3 14.9a1.1 1.1 0 0 0 .95 1.6h9.5a1.1 1.1 0 0 0 .95-1.6L11.5 7.7V3.5"/><path d="M6.2 12h7.6"/>',
  atencao: '<path d="M10 3.5 17.2 16a.7.7 0 0 1-.6 1H3.4a.7.7 0 0 1-.6-1L10 3.5Z"/><path d="M10 8.5v3.5M10 14.4v.1"/>',
  historico: '<path d="M3.6 10a6.5 6.5 0 1 0 1.9-4.6L3.5 7.3"/><path d="M3.5 3.8v3.5H7M10 6.5V10l2.5 1.5"/>',
  adicionar: '<path d="M10 4v12M4 10h12"/>',
  editar: '<path d="m12.4 4.6 3 3M4 16l.7-3.4L13.4 4a1.4 1.4 0 0 1 2 0l.6.6a1.4 1.4 0 0 1 0 2L7.4 15.3 4 16Z"/>',
  excluir: '<path d="M4 6h12M8 6V4.5h4V6M5.5 6l.7 9.6a1 1 0 0 0 1 .9h5.6a1 1 0 0 0 1-.9L14.5 6"/>',
  chave: '<circle cx="7" cy="12.5" r="3.5"/><path d="m9.5 10 6-6M13.5 6l2 2M12 7.5l1.5 1.5"/>',
  baixar: '<path d="M10 3.5v9M6.5 9 10 12.5 13.5 9M4 16.5h12"/>',
  informacao: '<circle cx="10" cy="10" r="7"/><path d="M10 9v4.5M10 6.5v.1"/>',
  erro: '<circle cx="10" cy="10" r="7"/><path d="M10 6.5V11M10 13.4v.1"/>',
  sucesso: '<circle cx="10" cy="10" r="7"/><path d="m7 10.2 2 2 4-4.2"/>',
  fechar: '<path d="m5 5 10 10M15 5 5 15"/>',
  voltar: '<path d="M16 10H4.5M9 5.5 4.5 10 9 14.5"/>',
  sensor: '<path d="M6.5 6.5a5 5 0 0 0 0 7M13.5 6.5a5 5 0 0 1 0 7M4.2 4.2a8.2 8.2 0 0 0 0 11.6M15.8 4.2a8.2 8.2 0 0 1 0 11.6"/><circle cx="10" cy="10" r="1.5"/>',
  escudo: '<path d="M10 3 4 5.2v4.6c0 3.4 2.5 6.1 6 7.2 3.5-1.1 6-3.8 6-7.2V5.2L10 3Z"/><path d="m7.5 10 1.8 1.8 3.2-3.4"/>',
  relogio: '<circle cx="10" cy="10" r="7"/><path d="M10 6v4l2.5 1.5"/>',
  'seta-direita': '<path d="m8 5 5 5-5 5"/>',
  pessoa: '<circle cx="10" cy="6.5" r="3"/><path d="M4 16.5c.6-3 3-4.5 6-4.5s5.4 1.5 6 4.5"/>',
};

// tamanho: '' (20 px), 'p' (16 px), 'g' (24 px) ou 'gg' (40 px).
export function icone(nome, tamanho = '') {
  const desenho = desenhos[nome] || desenhos.informacao;
  const classe = tamanho ? `icone icone-${tamanho}` : 'icone';
  return `<svg class="${classe}" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${desenho}</svg>`;
}

export function inserirIcones(raiz = document) {
  raiz.querySelectorAll('[data-icone]').forEach(elemento => {
    elemento.outerHTML = icone(elemento.dataset.icone, elemento.dataset.tamanho || '');
  });
}
