// Aba "Ocorrências manuais": situações observadas em campo pela equipe.
import { api } from './api.js';
import { estadoTela } from './estado.js';
import { carregarPontos, opcoesPontos } from './dados.js';
import { escaparHtml, formatarDataHora, seloSituacao, valorCampo } from './formatacao.js';
import {
  abrirDialogo, avisar, blocoCarregando, blocoErro, blocoEstado, campoFormulario, comBotaoOcupado, confirmarEmDialogo,
  fecharDialogo, focarPrimeiroErro, limparErros, linhaEstado, marcarErro, mostrarErroFormulario,
} from './interface.js';

const COLUNAS = 5;

export async function mostrarOcorrencias() {
  const corpo = document.getElementById('ocorrencias-linhas');
  if (!corpo) return;
  const situacao = valorCampo('ocorrencias-filtro') || 'abertas';
  corpo.innerHTML = linhaEstado(COLUNAS, blocoCarregando('Carregando ocorrências...'));
  try {
    const ocorrencias = await api.ocorrencias(situacao);
    if (!ocorrencias.length) {
      corpo.innerHTML = linhaEstado(COLUNAS, blocoEstado({
        nomeIcone: 'sucesso',
        titulo: situacao === 'abertas' ? 'Nenhuma ocorrência aberta' : 'Nenhuma ocorrência registrada',
        texto: 'Registre uma ocorrência quando a equipe observar em campo algo que as medições não mostram.',
      }));
      return;
    }
    corpo.innerHTML = ocorrencias.map(o => `
      <tr>
        <td data-label="Ponto"><span><strong>${escaparHtml(o.ponto_codigo)}</strong><span class="celula-secundaria">${escaparHtml(o.ponto_nome)}</span></span></td>
        <td data-label="Classificação">${seloSituacao(o.classificacao)}</td>
        <td data-label="Motivo">${escaparHtml(o.motivo)}</td>
        <td data-label="Aberta em" class="num"><span>${formatarDataHora(o.aberta_em)}<span class="celula-secundaria">${escaparHtml(o.aberta_por)}</span></span></td>
        <td data-label="Encerrada em">${o.encerrada_em
          ? `<span class="num">${formatarDataHora(o.encerrada_em)}<span class="celula-secundaria">${escaparHtml(o.encerrada_por)}</span></span>`
          : `<button class="botao" type="button" data-codigo="${escaparHtml(o.ponto_codigo)}" onclick="encerrarOcorrencia(${o.id}, this)">Encerrar</button>`}</td>
      </tr>`).join('');
  } catch (erro) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoErro(erro.message, 'mostrarOcorrencias()'));
  }
}

export async function abrirFormularioOcorrencia() {
  if (!estadoTela.pontos.length) await carregarPontos().catch(() => {});
  if (!estadoTela.pontos.some(ponto => ponto.ativo)) {
    avisar('Cadastre um ponto ativo primeiro.', 'atencao');
    return;
  }
  abrirDialogo({
    titulo: 'Registrar ocorrência manual',
    descricao: 'Use quando a equipe observar em campo uma situação que as medições não mostram. Enquanto estiver aberta, ela define a situação do ponto, inclusive no mapa público.',
    corpo: `
      <form id="form-ocorrencia" class="form-grade" novalidate onsubmit="event.preventDefault(); salvarOcorrencia(this)">
        <div class="ocupa-2" data-erro-form></div>
        ${campoFormulario({ id: 'ocorrencia-ponto', rotulo: 'Ponto', obrigatorio: true, controle: `<select class="selecao" id="ocorrencia-ponto" aria-describedby="ocorrencia-ponto-erro">${opcoesPontos()}</select>` })}
        ${campoFormulario({ id: 'ocorrencia-classificacao', rotulo: 'Classificação', obrigatorio: true, controle: '<select class="selecao" id="ocorrencia-classificacao" aria-describedby="ocorrencia-classificacao-erro"><option value="amarelo">Atenção</option><option value="laranja">Alerta</option><option value="vermelho" selected>Crítico</option></select>' })}
        ${campoFormulario({ id: 'ocorrencia-motivo', rotulo: 'Motivo', obrigatorio: true, ocupaDuas: true, controle: '<textarea class="area-texto" id="ocorrencia-motivo" rows="3" maxlength="2000" placeholder="Ex.: equipe verificou água sobre a pista" aria-describedby="ocorrencia-motivo-erro"></textarea>' })}
      </form>`,
    rodape: `<button class="botao" type="button" data-fechar-dialogo>Cancelar</button>
      <button class="botao perigo" type="submit" form="form-ocorrencia">Registrar ocorrência</button>`,
  });
}

export async function salvarOcorrencia(formulario) {
  limparErros(formulario);
  const motivo = valorCampo('ocorrencia-motivo');
  if (motivo.length < 3) {
    marcarErro('ocorrencia-motivo', 'Descreva o motivo (pelo menos 3 caracteres).');
    focarPrimeiroErro(formulario);
    return;
  }
  await comBotaoOcupado(document.querySelector('[form="form-ocorrencia"]'), async () => {
    try {
      await api.abrirOcorrencia(valorCampo('ocorrencia-ponto'), { classificacao: valorCampo('ocorrencia-classificacao'), motivo });
      fecharDialogo();
      avisar('Ocorrência registrada.', 'sucesso');
      mostrarOcorrencias();
    } catch (erro) {
      mostrarErroFormulario(formulario, erro.message);
    }
  }, 'Registrando...');
}

export async function encerrarOcorrencia(id, botao) {
  const codigo = botao.dataset.codigo; // lido do atributo, nunca montado dentro do código do onclick
  const confirmou = await confirmarEmDialogo({
    titulo: `Encerrar a ocorrência de ${codigo}?`,
    mensagem: 'O ponto volta a ser classificado pelas medições.',
    textoConfirmar: 'Encerrar',
  });
  if (!confirmou) return;
  await comBotaoOcupado(botao, async () => {
    try {
      await api.encerrarOcorrencia(id);
      avisar('Ocorrência encerrada.', 'sucesso');
      mostrarOcorrencias();
    } catch (erro) {
      avisar(erro.message, 'erro');
    }
  }, 'Encerrando...');
}
