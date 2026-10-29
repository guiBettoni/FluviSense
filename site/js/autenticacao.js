// Entrada e saída do operador.
import { api, sessao } from './api.js';
import { irPara } from './navegacao.js';
import { escaparHtml, valorCampo } from './formatacao.js';
import { avisar, comBotaoOcupado, focarPrimeiroErro, limparErros, marcarErro, mostrarErroFormulario } from './interface.js';

export async function entrar(formulario) {
  limparErros(formulario);
  const email = valorCampo('login-email').toLowerCase();
  const senha = document.getElementById('login-senha')?.value || '';
  if (!email) marcarErro('login-email', 'Informe o e-mail.');
  else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) marcarErro('login-email', 'Informe um e-mail válido.');
  if (!senha) marcarErro('login-senha', 'Informe a senha.');
  if (formulario.querySelector('[aria-invalid="true"]')) {
    focarPrimeiroErro(formulario);
    return;
  }
  await comBotaoOcupado(formulario.querySelector('[type="submit"]'), async () => {
    try {
      const resultado = await api.entrar(email, senha);
      sessao.salvar(resultado.token_acesso, resultado.usuario);
      formulario.reset();
      irPara('painel');
      avisar(`Bem-vindo, ${resultado.usuario.nome}.`, 'sucesso');
    } catch (erro) {
      sessao.limpar();
      mostrarErroFormulario(formulario, erro.message);
      document.getElementById('login-senha')?.select();
    }
  }, 'Entrando...');
}

export function sair() {
  sessao.limpar();
  avisar('Sessão encerrada.', 'informacao');
  irPara('inicio');
}

// Nome e iniciais do operador no topo do painel.
export function mostrarOperador() {
  const operador = sessao.operador();
  const nome = operador?.nome || operador?.email || 'Operador';
  const iniciais = nome.split(/\s+/).filter(Boolean).slice(0, 2).map(parte => parte[0]).join('').toUpperCase() || 'OP';
  const elemento = document.getElementById('operador');
  if (elemento) {
    elemento.innerHTML = `<span class="pessoa-iniciais" aria-hidden="true">${escaparHtml(iniciais)}</span><span class="pessoa-nome">${escaparHtml(nome)}</span>`;
    elemento.title = operador?.email || nome;
  }
}
