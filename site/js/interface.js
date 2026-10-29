// Componentes de interface reutilizáveis: diálogo, confirmação, aviso, estados e validação.
import { icone, inserirIcones } from './icones.js';
import { escaparHtml } from './formatacao.js';

// ---------- Avisos rápidos (canto da tela) ----------
// tipo: 'informacao', 'sucesso', 'atencao' ou 'erro'.

export function avisar(mensagem, tipo = 'informacao') {
  const raiz = document.getElementById('avisos');
  if (!raiz) return;
  const aviso = document.createElement('div');
  aviso.className = `aviso ${tipo}`;
  aviso.setAttribute('role', tipo === 'erro' ? 'alert' : 'status');
  aviso.innerHTML = `${icone(tipo)}<p>${escaparHtml(mensagem)}</p>
    <button class="botao discreto so-icone" type="button" aria-label="Fechar aviso">${icone('fechar', 'p')}</button>`;
  const remover = () => {
    aviso.classList.add('saindo');
    setTimeout(() => aviso.remove(), 220);
  };
  aviso.querySelector('button').addEventListener('click', remover);
  // No máximo 3 avisos na tela; o mais antigo sai primeiro.
  while (raiz.children.length >= 3) raiz.firstElementChild.remove();
  raiz.appendChild(aviso);
  setTimeout(remover, tipo === 'erro' ? 7000 : 4000);
}

// ---------- Diálogo ----------
// Diálogos com formulário não fecham ao clicar fora: só por Cancelar, Fechar, salvar
// ou Esc (que pede confirmação se algum campo foi alterado).

let dialogoAberto = null;

const FOCAVEIS = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function abrirDialogo({ titulo, descricao = '', corpo = '', rodape = '', largo = false, aoFechar = null, fixo = false }) {
  fecharDialogo({ forcar: true });
  const raiz = document.getElementById('janela');
  const idTitulo = `dialogo-titulo-${Date.now()}`;
  raiz.innerHTML = `
    <div class="dialogo-fundo">
      <div class="dialogo ${largo ? 'largo' : ''}" role="dialog" aria-modal="true" aria-labelledby="${idTitulo}">
        <div class="dialogo-cabecalho">
          <div>
            <h2 id="${idTitulo}">${titulo}</h2>
            ${descricao ? `<p>${descricao}</p>` : ''}
          </div>
          <button class="botao discreto so-icone" type="button" data-fechar-dialogo aria-label="Fechar">${icone('fechar')}</button>
        </div>
        <div class="dialogo-corpo">${corpo}</div>
        ${rodape ? `<div class="dialogo-rodape">${rodape}</div>` : ''}
      </div>
    </div>`;
  inserirIcones(raiz);
  const dialogo = raiz.querySelector('.dialogo');
  const formulario = dialogo.querySelector('form');
  dialogoAberto = {
    dialogo,
    formulario,
    aoFechar,
    origem: document.activeElement,
    inicial: formulario ? retratoDoFormulario(formulario) : '',
  };
  dialogo.querySelectorAll('[data-fechar-dialogo]').forEach(botao => botao.addEventListener('click', () => fecharDialogo()));
  // Clique no fundo escuro: fecha só diálogos sem formulário (avisos e resultados).
  raiz.querySelector('.dialogo-fundo').addEventListener('mousedown', evento => {
    if (evento.target === evento.currentTarget && !formulario && !fixo) fecharDialogo();
  });
  document.body.style.overflow = 'hidden';
  const primeiro = dialogo.querySelector('[autofocus]') || dialogo.querySelector(`.dialogo-corpo ${FOCAVEIS}`) || dialogo.querySelector(FOCAVEIS);
  primeiro?.focus();
  return dialogo;
}

export function fecharDialogo({ forcar = false } = {}) {
  if (!dialogoAberto) return;
  const { aoFechar, origem } = dialogoAberto;
  dialogoAberto = null;
  document.getElementById('janela').innerHTML = '';
  document.body.style.overflow = '';
  if (!forcar) {
    aoFechar?.();
    if (origem && document.contains(origem)) origem.focus();
  }
}

function retratoDoFormulario(formulario) {
  return JSON.stringify([...formulario.elements].map(campo => (campo.type === 'checkbox' ? campo.checked : campo.value)));
}

function formularioAlterado() {
  return Boolean(dialogoAberto?.formulario && retratoDoFormulario(dialogoAberto.formulario) !== dialogoAberto.inicial);
}

// Pede confirmação antes de descartar um formulário alterado (usado pelo Esc).
async function pedirParaFechar() {
  if (!dialogoAberto) return;
  if (!formularioAlterado()) {
    fecharDialogo();
    return;
  }
  const mesmoDialogo = dialogoAberto;
  const descartar = await confirmarDentroDoDialogo('Descartar o que foi preenchido?', '', 'Descartar');
  if (descartar && dialogoAberto === mesmoDialogo) fecharDialogo();
}

// Mini confirmação dentro do próprio diálogo, para não perder o formulário.
function confirmarDentroDoDialogo(mensagem, detalhe, textoAcao) {
  return new Promise(responder => {
    const rodape = dialogoAberto?.dialogo.querySelector('.dialogo-rodape');
    if (!rodape) return responder(true);
    const barra = document.createElement('div');
    barra.className = 'barra-mensagem atencao';
    barra.setAttribute('role', 'alert');
    barra.style.flex = '1 1 100%';
    barra.innerHTML = `${icone('atencao')}<div style="flex:1"><strong>${escaparHtml(mensagem)}</strong>${detalhe ? `<p>${escaparHtml(detalhe)}</p>` : ''}</div>
      <button class="botao" type="button" data-continuar>Continuar editando</button>
      <button class="botao perigo" type="button" data-descartar>${escaparHtml(textoAcao)}</button>`;
    rodape.prepend(barra);
    const concluir = valor => { barra.remove(); responder(valor); };
    barra.querySelector('[data-continuar]').addEventListener('click', () => concluir(false));
    barra.querySelector('[data-descartar]').addEventListener('click', () => concluir(true));
    barra.querySelector('[data-continuar]').focus();
  });
}

document.addEventListener('keydown', evento => {
  if (!dialogoAberto) return;
  if (evento.key === 'Escape') {
    evento.preventDefault();
    pedirParaFechar();
    return;
  }
  if (evento.key === 'Tab') {
    // Mantém o foco do teclado dentro do diálogo.
    const itens = [...dialogoAberto.dialogo.querySelectorAll(FOCAVEIS)].filter(item => item.offsetParent !== null);
    if (!itens.length) return;
    const primeiro = itens[0];
    const ultimo = itens[itens.length - 1];
    if (evento.shiftKey && document.activeElement === primeiro) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primeiro.focus();
    }
  }
});

// Confirmação que respeita o diálogo aberto: se houver um, pergunta dentro dele (sem perder o
// formulário); se não houver, abre um diálogo de confirmação.
export function confirmarAcao(opcoes) {
  if (dialogoAberto?.dialogo.querySelector('.dialogo-rodape')) {
    return confirmarDentroDoDialogo(opcoes.titulo, opcoes.mensagem, opcoes.textoConfirmar || 'Confirmar');
  }
  return confirmarEmDialogo(opcoes);
}

// Confirmação para ações destrutivas ou irreversíveis. Devolve uma Promise com true ou false.
export function confirmarEmDialogo({ titulo, mensagem, textoConfirmar = 'Confirmar', perigo = false }) {
  return new Promise(responder => {
    let respondido = false;
    const responderUmaVez = valor => {
      if (respondido) return;
      respondido = true;
      responder(valor);
    };
    const dialogo = abrirDialogo({
      titulo: escaparHtml(titulo),
      corpo: `<p>${escaparHtml(mensagem)}</p>`,
      rodape: `<button class="botao" type="button" data-cancelar>Cancelar</button>
        <button class="botao ${perigo ? 'perigo' : 'principal'}" type="button" data-confirmar>${escaparHtml(textoConfirmar)}</button>`,
      aoFechar: () => responderUmaVez(false),
    });
    dialogo.querySelector('[data-cancelar]').addEventListener('click', () => fecharDialogo());
    dialogo.querySelector('[data-confirmar]').addEventListener('click', () => {
      responderUmaVez(true);
      fecharDialogo();
    });
    dialogo.querySelector('[data-cancelar]').focus();
  });
}

// ---------- Botão ocupado (evita clique duplo durante o salvamento) ----------

export async function comBotaoOcupado(botao, tarefa, textoOcupado = 'Salvando...') {
  if (!botao) return tarefa();
  const conteudoOriginal = botao.innerHTML;
  botao.disabled = true;
  botao.classList.add('ocupado');
  botao.innerHTML = `<span class="girando" aria-hidden="true"></span>${escaparHtml(textoOcupado)}`;
  try {
    return await tarefa();
  } finally {
    if (document.contains(botao)) {
      botao.disabled = false;
      botao.classList.remove('ocupado');
      botao.innerHTML = conteudoOriginal;
    }
  }
}

// ---------- Estados de carregamento, vazio e erro ----------
// tipo: 'vazio', 'carregando' ou 'erro'.

export function blocoEstado({ tipo = 'vazio', nomeIcone = 'informacao', titulo = '', texto = '', acao = '', compacto = false }) {
  const imagem = tipo === 'carregando' ? '<span class="girando" aria-hidden="true"></span>' : icone(tipo === 'erro' ? 'erro' : nomeIcone, 'gg');
  return `<div class="estado ${tipo} ${compacto ? 'compacto' : ''}" ${tipo === 'carregando' ? 'role="status" aria-live="polite"' : ''}>
    ${imagem}
    ${titulo ? `<strong>${escaparHtml(titulo)}</strong>` : ''}
    ${texto ? `<p>${escaparHtml(texto)}</p>` : ''}
    ${acao}
  </div>`;
}

export function blocoCarregando(texto = 'Carregando...') {
  return blocoEstado({ tipo: 'carregando', texto, compacto: true });
}

export function blocoErro(mensagem, tentarDeNovo = '') {
  return blocoEstado({
    tipo: 'erro',
    titulo: 'Não foi possível carregar',
    texto: mensagem,
    acao: tentarDeNovo ? `<button class="botao" type="button" onclick="${tentarDeNovo}">Tentar de novo</button>` : '',
    compacto: true,
  });
}

export function linhaEstado(colunas, html) {
  return `<tr><td class="celula-estado" colspan="${colunas}">${html}</td></tr>`;
}

// ---------- Validação de formulário ----------

export function limparErros(formulario) {
  formulario?.querySelectorAll('[aria-invalid="true"]').forEach(campo => campo.removeAttribute('aria-invalid'));
  formulario?.querySelectorAll('.campo-erro').forEach(erro => { erro.textContent = ''; });
  formulario?.querySelector('[data-erro-form]')?.replaceChildren();
}

export function marcarErro(id, mensagem) {
  const campo = document.getElementById(id);
  if (!campo) return;
  campo.setAttribute('aria-invalid', 'true');
  const erro = document.getElementById(`${id}-erro`);
  if (erro) erro.textContent = mensagem;
}

// Mostra o erro devolvido pela API dentro do próprio formulário.
export function mostrarErroFormulario(formulario, mensagem) {
  const espaco = formulario?.querySelector('[data-erro-form]');
  if (!espaco) {
    avisar(mensagem, 'erro');
    return;
  }
  espaco.innerHTML = `<div class="barra-mensagem erro" role="alert">${icone('erro')}<div>${escaparHtml(mensagem)}</div></div>`;
  espaco.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

export function focarPrimeiroErro(formulario) {
  formulario?.querySelector('[aria-invalid="true"]')?.focus();
}

// ---------- Campos de formulário ----------
// Gera um campo com rótulo, dica e espaço para erro, ligados por aria-describedby.
export function campoFormulario({ id, rotulo, valor = '', tipo = 'text', obrigatorio = false, dica = '', atributos = '', ocupaDuas = false, controle = '' }) {
  const descritoPor = [dica ? `${id}-dica` : '', `${id}-erro`].filter(Boolean).join(' ');
  const entrada = controle || `<input class="entrada" id="${id}" name="${id}" type="${tipo}" value="${escaparHtml(valor ?? '')}" ${obrigatorio ? 'required' : ''} aria-describedby="${descritoPor}" ${atributos}>`;
  return `<div class="campo ${ocupaDuas ? 'ocupa-2' : ''}">
    <label class="campo-rotulo" for="${id}">${rotulo}${obrigatorio ? '<span class="obrigatorio" aria-hidden="true">*</span>' : ''}</label>
    ${entrada}
    ${dica ? `<span class="campo-dica" id="${id}-dica">${dica}</span>` : ''}
    <span class="campo-erro" id="${id}-erro" role="alert"></span>
  </div>`;
}
