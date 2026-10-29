// Comunicação com a API. Cada função abaixo chama uma rota de /api.
import { CONFIGURACAO } from './configuracao.js';

const CHAVE_TOKEN = 'fluvisense_token_operador';
const CHAVE_OPERADOR = 'fluvisense_operador';

function enderecoApi() {
  const endereco = CONFIGURACAO.api.endereco?.trim() || '';
  if (!endereco) throw new Error('Configure FLUVISENSE_CONFIGURACAO.enderecoApi em index.html para conectar à API.');
  return endereco.replace(/\/$/, '');
}

function lerArmazenamento(chave) {
  try {
    return localStorage.getItem(chave) || '';
  } catch {
    return '';
  }
}

function gravarArmazenamento(chave, valor) {
  try {
    if (valor === null) localStorage.removeItem(chave);
    else localStorage.setItem(chave, valor);
  } catch {
    // Navegação privada pode bloquear o armazenamento; o login só não sobrevive ao recarregar.
  }
}

async function requisicao(caminho, { metodo = 'GET', corpo, autenticada = true } = {}) {
  const cabecalhos = {};
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json';
  const token = lerArmazenamento(CHAVE_TOKEN);
  if (autenticada && token) cabecalhos.Authorization = `Bearer ${token}`;
  let resposta;
  try {
    resposta = await fetch(`${enderecoApi()}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new Error('Não foi possível conectar à API.');
  }
  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => ({}));
  if (resposta.status === 401 && autenticada && token) {
    sessao.limpar();
    window.dispatchEvent(new CustomEvent('fluvisense:sessao-expirada'));
  }
  if (!resposta.ok) throw new Error(mensagemDeErro(dados));
  return dados;
}

// A API responde erros como {"detalhe": "texto"} ou {"detalhe": [{"campo": ..., "mensagem": ...}]}.
function mensagemDeErro(dados) {
  const detalhe = dados?.detalhe;
  if (typeof detalhe === 'string') return detalhe;
  if (Array.isArray(detalhe)) return detalhe.map(item => String(item.mensagem || '')).join(' ');
  return 'Falha de comunicação com a API.';
}

function parametros(valores) {
  const busca = new URLSearchParams();
  Object.entries(valores).forEach(([nome, valor]) => {
    if (valor !== null && valor !== undefined && valor !== '') busca.set(nome, valor);
  });
  const texto = busca.toString();
  return texto ? `?${texto}` : '';
}

export const sessao = {
  ativa: () => Boolean(lerArmazenamento(CHAVE_TOKEN)),
  operador() {
    try {
      return JSON.parse(lerArmazenamento(CHAVE_OPERADOR) || 'null');
    } catch {
      return null;
    }
  },
  salvar(token, operador) {
    gravarArmazenamento(CHAVE_TOKEN, token);
    gravarArmazenamento(CHAVE_OPERADOR, JSON.stringify(operador));
  },
  limpar() {
    gravarArmazenamento(CHAVE_TOKEN, null);
    gravarArmazenamento(CHAVE_OPERADOR, null);
  },
};

export const api = {
  entrar: (email, senha) => requisicao('/autenticacao/login', { metodo: 'POST', corpo: { email, senha }, autenticada: false }),
  operador: () => requisicao('/autenticacao/operador'),

  pontosPublicos: () => requisicao('/publico/pontos', { autenticada: false }),
  rios: () => requisicao('/rios', { autenticada: false }),
  criarRio: corpo => requisicao('/rios', { metodo: 'POST', corpo }),
  alterarRio: (id, corpo) => requisicao(`/rios/${id}`, { metodo: 'PUT', corpo }),
  excluirRio: id => requisicao(`/rios/${id}`, { metodo: 'DELETE' }),

  pontos: () => requisicao('/pontos'),
  ponto: id => requisicao(`/pontos/${id}`),
  criarPonto: corpo => requisicao('/pontos', { metodo: 'POST', corpo }),
  alterarPonto: (id, corpo) => requisicao(`/pontos/${id}`, { metodo: 'PUT', corpo }),
  desativarPonto: id => requisicao(`/pontos/${id}`, { metodo: 'DELETE' }),
  excluirPonto: id => requisicao(`/pontos/${id}/definitivo`, { metodo: 'DELETE' }),
  gerarChaveSensor: id => requisicao(`/pontos/${id}/chave-sensor`, { metodo: 'POST' }),

  medicoes: (id, filtros = {}) => requisicao(`/pontos/${id}/medicoes${parametros(filtros)}`),
  criarMedicao: (id, corpo) => requisicao(`/pontos/${id}/medicoes`, { metodo: 'POST', corpo }),
  simular: (id, corpo) => requisicao(`/pontos/${id}/simulacoes`, { metodo: 'POST', corpo }),
  apagarSimuladas: id => requisicao(`/pontos/${id}/medicoes/simuladas`, { metodo: 'DELETE' }),

  ocorrencias: situacao => requisicao(`/ocorrencias${parametros({ situacao })}`),
  abrirOcorrencia: (pontoId, corpo) => requisicao(`/pontos/${pontoId}/ocorrencias`, { metodo: 'POST', corpo }),
  encerrarOcorrencia: id => requisicao(`/ocorrencias/${id}/encerrar`, { metodo: 'PUT' }),

  auditoria: () => requisicao('/auditoria'),
};
