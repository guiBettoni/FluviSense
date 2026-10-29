// Aba "Auditoria": quem fez o quê e quando.
import { api } from './api.js';
import { baixarCsv, escaparHtml, formatarDataHora } from './formatacao.js';
import { avisar, blocoCarregando, blocoErro, blocoEstado, linhaEstado } from './interface.js';

const COLUNAS = 5;
let ultimosEventos = [];

export async function mostrarAuditoria() {
  const corpo = document.getElementById('auditoria-linhas');
  if (!corpo) return;
  corpo.innerHTML = linhaEstado(COLUNAS, blocoCarregando('Carregando registros...'));
  try {
    ultimosEventos = await api.auditoria();
    corpo.innerHTML = ultimosEventos.map(evento => `
      <tr>
        <td data-label="Data" class="num">${formatarDataHora(evento.criado_em)}</td>
        <td data-label="Usuário">${escaparHtml(evento.autor)}</td>
        <td data-label="Ação"><span class="selo simples informacao">${escaparHtml(evento.acao)}</span></td>
        <td data-label="Entidade">${escaparHtml(evento.entidade)}</td>
        <td data-label="Detalhes"><span class="texto-mono">${escaparHtml(evento.detalhes || '–')}</span></td>
      </tr>`).join('') || linhaEstado(COLUNAS, blocoEstado({ nomeIcone: 'historico', titulo: 'Nenhum registro ainda', texto: 'As alterações feitas no painel aparecem aqui.' }));
  } catch (erro) {
    corpo.innerHTML = linhaEstado(COLUNAS, blocoErro(erro.message, 'mostrarAuditoria()'));
  }
}

export function exportarAuditoria() {
  if (!ultimosEventos.length) {
    avisar('Não há registros para exportar.', 'atencao');
    return;
  }
  baixarCsv('auditoria-fluvisense.csv', ['Data', 'Usuário', 'Ação', 'Entidade', 'Detalhes'],
    ultimosEventos.map(evento => [evento.criado_em, evento.autor, evento.acao, evento.entidade, evento.detalhes || '']));
  avisar(`${ultimosEventos.length} registros exportados.`, 'sucesso');
}
