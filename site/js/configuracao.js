const configuracaoDaPagina = globalThis.FLUVISENSE_CONFIGURACAO || {};
const servidor = globalThis.location?.hostname || '';
const ehLocal = ['localhost', '127.0.0.1'].includes(servidor);

export const CONFIGURACAO = {
  centro: [-27.645, -48.67], // Palhoça/SC
  aproximacao: 12,
  api: {
    // No próprio computador usa a API na porta 8001; fora dele, o endereço definido em index.html.
    endereco: ehLocal ? `http://${servidor}:8001/api` : configuracaoDaPagina.enderecoApi,
    intervaloAtualizacaoMs: Number(configuracaoDaPagina.intervaloAtualizacaoMs) || 15000,
  },
};
