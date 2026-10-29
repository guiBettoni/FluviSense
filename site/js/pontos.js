// Aba "Rios e pontos": cadastro de rios, pontos de monitoramento e chave do sensor.
import { api } from './api.js';
import { estadoTela } from './estado.js';
import { buscarPonto, carregarPontos, carregarRios, opcoesRios } from './dados.js';
import { escaparHtml, formatarCm, numeroOuNulo, plural, seloSituacao, valorCampo } from './formatacao.js';
import { inserirIcones } from './icones.js';
import {
  abrirDialogo, avisar, blocoCarregando, blocoErro, blocoEstado, campoFormulario, comBotaoOcupado, confirmarAcao,
  fecharDialogo, focarPrimeiroErro, limparErros, marcarErro, mostrarErroFormulario,
} from './interface.js';

let jaCarregou = false;

export async function mostrarAbaPontos() {
  const listaRios = document.getElementById('rios-lista');
  const gradePontos = document.getElementById('pontos-grade');
  if (!jaCarregou) {
    if (gradePontos) gradePontos.innerHTML = blocoCarregando('Carregando pontos...');
    if (listaRios) listaRios.innerHTML = `<li>${blocoCarregando('Carregando rios...')}</li>`;
  }
  try {
    await Promise.all([carregarRios(), carregarPontos()]);
    jaCarregou = true;
  } catch (erro) {
    if (gradePontos) gradePontos.innerHTML = blocoErro(erro.message, 'mostrarAbaPontos()');
    if (listaRios) listaRios.innerHTML = '';
    return;
  }
  if (listaRios) {
    listaRios.innerHTML = estadoTela.rios.map(rio => `
      <li class="rio-item">
        <span data-icone="agua"></span>
        <div class="rio-dados">
          <strong>${escaparHtml(rio.nome)}</strong>
          <p>${plural(rio.quantidade_pontos, 'ponto', 'pontos')}${rio.observacoes ? ` · ${escaparHtml(rio.observacoes)}` : ''}</p>
        </div>
        <button class="botao discreto so-icone" type="button" onclick="abrirFormularioRio(${rio.id})" aria-label="Editar ${escaparHtml(rio.nome)}" title="Editar"><span data-icone="editar"></span></button>
      </li>`).join('') || `<li>${blocoEstado({ nomeIcone: 'agua', titulo: 'Nenhum rio', texto: 'Cadastre um rio antes dos pontos.', compacto: true, acao: '<button class="botao principal" type="button" onclick="abrirFormularioRio()">Novo rio</button>' })}</li>`;
  }
  if (gradePontos) {
    gradePontos.innerHTML = estadoTela.pontos.map(cartaoPonto).join('') || blocoEstado({
      nomeIcone: 'local',
      titulo: 'Nenhum ponto cadastrado',
      texto: estadoTela.rios.length ? 'Cadastre o primeiro ponto de monitoramento.' : 'Primeiro cadastre um rio, ao lado.',
      acao: estadoTela.rios.length ? '<button class="botao principal" type="button" onclick="abrirFormularioPonto()">Novo ponto</button>' : '',
    });
  }
  inserirIcones(document.getElementById('aba-pontos'));
}

function cartaoPonto(ponto) {
  const criterios = ponto.distancia_atencao_cm === null
    ? 'Sem critérios configurados'
    : (ponto.criterios_provisorios ? 'Critérios provisórios' : 'Critérios com referência');
  return `
    <article class="cartao ponto-cartao ${ponto.ativo ? '' : 'inativo'}">
      <div class="ponto-cartao-topo">
        <div>
          <span class="codigo">${escaparHtml(ponto.codigo)}</span>
          <h3>${escaparHtml(ponto.nome)}</h3>
          <p class="texto-pequeno texto-apagado">${escaparHtml(ponto.rio_nome || 'Sem rio (ponto migrado)')}${ponto.bairro ? ` · ${escaparHtml(ponto.bairro)}` : ''}</p>
        </div>
        ${ponto.ativo ? seloSituacao(ponto.estado_real.situacao) : '<span class="selo inativo">Desativado</span>'}
      </div>
      <dl class="lista-detalhes" aria-label="Critérios de classificação">
        <div><dt>Atenção ≤</dt><dd>${formatarCm(ponto.distancia_atencao_cm)}</dd></div>
        <div><dt>Alerta ≤</dt><dd>${formatarCm(ponto.distancia_alerta_cm)}</dd></div>
        <div><dt>Crítico ≤</dt><dd>${formatarCm(ponto.distancia_critica_cm)}</dd></div>
      </dl>
      <p class="nota">${criterios} · desatualiza após ${ponto.minutos_para_desatualizar} min · ${ponto.possui_chave_sensor ? 'sensor com chave' : 'sem chave de sensor'}</p>
      <button class="botao" type="button" onclick="abrirFormularioPonto(${ponto.id})"><span data-icone="editar"></span>Editar</button>
    </article>`;
}

// ---------- Rios ----------

export function abrirFormularioRio(id = null) {
  const rio = estadoTela.rios.find(item => item.id === id);
  abrirDialogo({
    titulo: rio ? 'Editar rio' : 'Novo rio',
    descricao: rio ? `${plural(rio.quantidade_pontos, 'ponto ligado', 'pontos ligados')} a este rio.` : '',
    corpo: `
      <form id="form-rio" class="form-grade" novalidate onsubmit="event.preventDefault(); salvarRio(this, ${rio ? rio.id : 'null'})">
        <div class="ocupa-2" data-erro-form></div>
        ${campoFormulario({ id: 'rio-nome', rotulo: 'Nome', valor: rio?.nome || '', obrigatorio: true, ocupaDuas: true, atributos: 'maxlength="120" autocomplete="off"' })}
        ${campoFormulario({ id: 'rio-observacoes', rotulo: 'Observações', ocupaDuas: true, controle: `<textarea class="area-texto" id="rio-observacoes" rows="3" maxlength="1000" aria-describedby="rio-observacoes-erro">${escaparHtml(rio?.observacoes || '')}</textarea>` })}
      </form>`,
    rodape: `${rio ? `<button class="botao discreto texto-perigo" type="button" onclick="excluirRio(${rio.id})"><span data-icone="excluir"></span>Excluir rio</button><span class="espacador"></span>` : ''}
      <button class="botao" type="button" data-fechar-dialogo>Cancelar</button>
      <button class="botao principal" type="submit" form="form-rio">Salvar</button>`,
  });
}

export async function excluirRio(id) {
  const rio = estadoTela.rios.find(item => item.id === id);
  const formulario = document.getElementById('form-rio');
  if (!rio) return;
  limparErros(formulario);
  // Regra da API: rio com pontos ligados não pode ser excluído. Avisamos antes de perguntar.
  if (rio.quantidade_pontos > 0) {
    mostrarErroFormulario(formulario, `O rio ${rio.nome} tem ${plural(rio.quantidade_pontos, 'ponto ligado', 'pontos ligados')} (contando os desativados). Mude o rio desses pontos ou exclua-os antes de excluir o rio.`);
    return;
  }
  const confirmou = await confirmarAcao({
    titulo: `Excluir o rio ${rio.nome}?`,
    mensagem: 'Essa ação não pode ser desfeita.',
    textoConfirmar: 'Excluir rio',
    perigo: true,
  });
  if (!confirmou) return;
  try {
    await api.excluirRio(id);
    fecharDialogo({ forcar: true });
    avisar(`Rio ${rio.nome} excluído.`, 'sucesso');
  } catch (erro) {
    mostrarErroFormulario(formulario, erro.message);
  }
  mostrarAbaPontos();
}

export async function salvarRio(formulario, id) {
  limparErros(formulario);
  const corpo = { nome: valorCampo('rio-nome'), observacoes: valorCampo('rio-observacoes') || null };
  if (corpo.nome.length < 2) {
    marcarErro('rio-nome', 'Informe o nome do rio (pelo menos 2 letras).');
    focarPrimeiroErro(formulario);
    return;
  }
  await comBotaoOcupado(document.querySelector('[form="form-rio"]'), async () => {
    try {
      if (id) await api.alterarRio(id, corpo);
      else await api.criarRio(corpo);
      fecharDialogo();
      avisar(id ? 'Rio atualizado.' : 'Rio cadastrado.', 'sucesso');
      mostrarAbaPontos();
    } catch (erro) {
      mostrarErroFormulario(formulario, erro.message);
    }
  });
}

// ---------- Pontos ----------

export async function abrirFormularioPonto(id = null) {
  if (!estadoTela.rios.length) await carregarRios().catch(() => {});
  if (!estadoTela.rios.length) {
    avisar('Cadastre um rio antes de cadastrar pontos.', 'atencao');
    abrirFormularioRio();
    return;
  }
  const ponto = id ? buscarPonto(id) : null;
  const cm = 'type="number" inputmode="decimal" step="0.01" min="0.01"';
  const valor = campo => ponto?.[campo] ?? '';
  const acoes = ponto ? `
      ${ponto.ativo
        ? `<button class="botao discreto" type="button" onclick="desativarPonto(${ponto.id})"><span data-icone="sair"></span>Desativar</button>`
        : `<button class="botao discreto" type="button" onclick="reativarPonto(${ponto.id})"><span data-icone="sucesso"></span>Reativar</button>`}
      <button class="botao discreto texto-perigo" type="button" onclick="excluirPonto(${ponto.id})"><span data-icone="excluir"></span>Excluir</button>
      <span class="espacador"></span>` : '';
  abrirDialogo({
    titulo: ponto ? `Editar ponto ${escaparHtml(ponto.codigo)}` : 'Novo ponto de monitoramento',
    descricao: ponto ? escaparHtml(ponto.nome) : 'Os campos com * são obrigatórios.',
    largo: true,
    corpo: `
      <form id="form-ponto" class="form-grade" novalidate onsubmit="event.preventDefault(); salvarPonto(this, ${ponto ? ponto.id : 'null'})">
        <div class="ocupa-2" data-erro-form></div>
        <div class="form-secao"><h3>Identificação e local</h3></div>
        ${ponto ? '' : campoFormulario({ id: 'pt-codigo', rotulo: 'Código', obrigatorio: true, dica: 'Letras, números, hífen e sublinhado. Ex.: CUB-01', atributos: 'maxlength="50" autocomplete="off"' })}
        ${campoFormulario({ id: 'pt-nome', rotulo: 'Nome do ponto', valor: valor('nome'), obrigatorio: true, atributos: 'maxlength="120"' })}
        ${campoFormulario({ id: 'pt-rio', rotulo: 'Rio', obrigatorio: true, controle: `<select class="selecao" id="pt-rio" required aria-describedby="pt-rio-erro"><option value="">Selecione...</option>${opcoesRios(ponto?.rio_id)}</select>` })}
        ${campoFormulario({ id: 'pt-bairro', rotulo: 'Bairro', valor: valor('bairro'), atributos: 'maxlength="120"' })}
        ${campoFormulario({ id: 'pt-local', rotulo: 'Descrição do local', valor: valor('descricao_local'), ocupaDuas: true, atributos: 'maxlength="255"' })}
        ${campoFormulario({ id: 'pt-latitude', rotulo: 'Latitude', valor: valor('latitude'), obrigatorio: true, tipo: 'number', dica: 'Ex.: -27.645', atributos: 'step="0.000001" min="-90" max="90" inputmode="decimal"' })}
        ${campoFormulario({ id: 'pt-longitude', rotulo: 'Longitude', valor: valor('longitude'), obrigatorio: true, tipo: 'number', dica: 'Ex.: -48.67', atributos: 'step="0.000001" min="-180" max="180" inputmode="decimal"' })}

        <div class="form-secao">
          <h3>Critérios de classificação</h3>
          <p class="texto-pequeno texto-apagado">Distância sensor → água. Quanto menor a distância, mais perto a água está. Preencha os três (atenção &gt; alerta &gt; crítico) ou deixe os três vazios. O FluviSense não fornece limiares oficiais.</p>
        </div>
        ${campoFormulario({ id: 'pt-atencao', rotulo: 'Atenção quando ≤ (cm)', valor: valor('distancia_atencao_cm'), tipo: 'number', atributos: cm })}
        ${campoFormulario({ id: 'pt-alerta', rotulo: 'Alerta quando ≤ (cm)', valor: valor('distancia_alerta_cm'), tipo: 'number', atributos: cm })}
        ${campoFormulario({ id: 'pt-critica', rotulo: 'Crítico quando ≤ (cm)', valor: valor('distancia_critica_cm'), tipo: 'number', atributos: cm })}
        <div class="campo"><span class="campo-rotulo" aria-hidden="true">&nbsp;</span>
          <label class="caixa-selecao"><input id="pt-provisorios" type="checkbox" ${ponto?.criterios_provisorios === false ? '' : 'checked'}><span>Critérios provisórios (sem referência validada)</span></label>
        </div>
        ${campoFormulario({ id: 'pt-justificativa', rotulo: 'Origem ou justificativa dos critérios', ocupaDuas: true, controle: `<textarea class="area-texto" id="pt-justificativa" rows="2" maxlength="1000" aria-describedby="pt-justificativa-erro">${escaparHtml(ponto?.justificativa_criterios || '')}</textarea>` })}

        <div class="form-secao">
          <h3>Validação das medições</h3>
          <p class="texto-pequeno texto-apagado">Fora da faixa mínima e máxima, a leitura é marcada como inválida. Um salto maior que o limite marca a leitura como suspeita.</p>
        </div>
        ${campoFormulario({ id: 'pt-minima', rotulo: 'Distância mínima válida (cm)', valor: valor('distancia_minima_valida_cm'), tipo: 'number', atributos: cm })}
        ${campoFormulario({ id: 'pt-maxima', rotulo: 'Distância máxima válida (cm)', valor: valor('distancia_maxima_valida_cm'), tipo: 'number', atributos: cm })}
        ${campoFormulario({ id: 'pt-salto', rotulo: 'Salto máximo entre leituras (cm)', valor: valor('salto_maximo_cm'), tipo: 'number', dica: 'Vazio = 50% da referência', atributos: cm })}
        ${campoFormulario({ id: 'pt-desatualizar', rotulo: 'Desatualizado após (min)', valor: ponto?.minutos_para_desatualizar ?? 720, tipo: 'number', obrigatorio: true, dica: '720 min = 12 horas', atributos: 'min="1" max="43200" step="1" inputmode="numeric"' })}
        ${ponto ? `
        <div class="form-secao">
          <h3>Sensor</h3>
          <p class="texto-pequeno texto-apagado">${ponto.possui_chave_sensor ? 'Este ponto já tem uma chave. Trocar invalida a chave atual.' : 'Gere uma chave para um sensor enviar medições reais deste ponto.'}</p>
        </div>
        <div class="ocupa-2"><button class="botao" type="button" onclick="gerarChaveSensor(${ponto.id})"><span data-icone="chave"></span>${ponto.possui_chave_sensor ? 'Trocar chave do sensor' : 'Gerar chave do sensor'}</button></div>` : ''}
      </form>`,
    rodape: `${acoes}<button class="botao" type="button" data-fechar-dialogo>Cancelar</button>
      <button class="botao principal" type="submit" form="form-ponto">Salvar</button>`,
  });
}

// Validação no navegador, com as mesmas regras da API, para mostrar o erro no campo certo.
function lerFormularioPonto(formulario, novo) {
  limparErros(formulario);
  // Cada campo numérico da API: [id do campo na tela, valor digitado convertido em número].
  const numeros = {
    latitude: ['pt-latitude', numeroOuNulo(valorCampo('pt-latitude'))],
    longitude: ['pt-longitude', numeroOuNulo(valorCampo('pt-longitude'))],
    distancia_atencao_cm: ['pt-atencao', numeroOuNulo(valorCampo('pt-atencao'))],
    distancia_alerta_cm: ['pt-alerta', numeroOuNulo(valorCampo('pt-alerta'))],
    distancia_critica_cm: ['pt-critica', numeroOuNulo(valorCampo('pt-critica'))],
    distancia_minima_valida_cm: ['pt-minima', numeroOuNulo(valorCampo('pt-minima'))],
    distancia_maxima_valida_cm: ['pt-maxima', numeroOuNulo(valorCampo('pt-maxima'))],
    salto_maximo_cm: ['pt-salto', numeroOuNulo(valorCampo('pt-salto'))],
    minutos_para_desatualizar: ['pt-desatualizar', numeroOuNulo(valorCampo('pt-desatualizar'))],
  };
  Object.values(numeros).forEach(([id, numero]) => {
    if (Number.isNaN(numero)) marcarErro(id, 'Use apenas números (ex.: 120 ou 120,5).');
  });
  const n = campo => numeros[campo][1];
  if (novo) {
    const codigo = valorCampo('pt-codigo');
    if (!codigo) marcarErro('pt-codigo', 'Informe o código do ponto.');
    else if (!/^[A-Za-z0-9_-]+$/.test(codigo)) marcarErro('pt-codigo', 'Use só letras, números, hífen e sublinhado.');
  }
  if (valorCampo('pt-nome').length < 2) marcarErro('pt-nome', 'Informe o nome do ponto.');
  if (!valorCampo('pt-rio')) marcarErro('pt-rio', 'Selecione o rio.');
  if (n('latitude') === null) marcarErro('pt-latitude', 'Informe a latitude.');
  else if (n('latitude') < -90 || n('latitude') > 90) marcarErro('pt-latitude', 'A latitude vai de -90 a 90.');
  if (n('longitude') === null) marcarErro('pt-longitude', 'Informe a longitude.');
  else if (n('longitude') < -180 || n('longitude') > 180) marcarErro('pt-longitude', 'A longitude vai de -180 a 180.');

  const criterios = [n('distancia_atencao_cm'), n('distancia_alerta_cm'), n('distancia_critica_cm')];
  const preenchidos = criterios.filter(valor => valor !== null && !Number.isNaN(valor)).length;
  if (preenchidos > 0 && preenchidos < 3) {
    ['pt-atencao', 'pt-alerta', 'pt-critica'].forEach((id, i) => {
      if (criterios[i] === null) marcarErro(id, 'Preencha os três critérios ou deixe os três vazios.');
    });
  } else if (preenchidos === 3 && !(criterios[0] > criterios[1] && criterios[1] > criterios[2] && criterios[2] > 0)) {
    marcarErro('pt-critica', 'A ordem precisa ser atenção > alerta > crítico > 0.');
  }
  if (n('distancia_minima_valida_cm') !== null && n('distancia_maxima_valida_cm') !== null && n('distancia_minima_valida_cm') >= n('distancia_maxima_valida_cm')) {
    marcarErro('pt-maxima', 'A máxima precisa ser maior que a mínima.');
  }
  const minutos = n('minutos_para_desatualizar');
  if (minutos === null || minutos < 1 || minutos > 43200 || !Number.isInteger(minutos)) marcarErro('pt-desatualizar', 'Use um número inteiro entre 1 e 43.200.');

  if (formulario.querySelector('[aria-invalid="true"]')) {
    focarPrimeiroErro(formulario);
    return null;
  }
  const corpo = Object.fromEntries(Object.entries(numeros).map(([campo, [, numero]]) => [campo, numero]));
  Object.assign(corpo, {
    nome: valorCampo('pt-nome'),
    rio_id: Number(valorCampo('pt-rio')),
    bairro: valorCampo('pt-bairro') || null,
    descricao_local: valorCampo('pt-local') || null,
    criterios_provisorios: Boolean(document.getElementById('pt-provisorios')?.checked),
    justificativa_criterios: valorCampo('pt-justificativa') || null,
  });
  if (novo) corpo.codigo = valorCampo('pt-codigo');
  return corpo;
}

export async function salvarPonto(formulario, id) {
  const corpo = lerFormularioPonto(formulario, !id);
  if (!corpo) return;
  await comBotaoOcupado(document.querySelector('[form="form-ponto"]'), async () => {
    try {
      if (id) await api.alterarPonto(id, corpo);
      else await api.criarPonto(corpo);
      fecharDialogo();
      avisar(id ? 'Configuração salva.' : 'Ponto cadastrado.', 'sucesso');
      mostrarAbaPontos();
    } catch (erro) {
      mostrarErroFormulario(formulario, erro.message);
    }
  });
}

// Mostra o erro no formulário do ponto, se ele estiver aberto; senão, num aviso.
function mostrarErroDoPonto(mensagem) {
  const formulario = document.getElementById('form-ponto');
  if (formulario) mostrarErroFormulario(formulario, mensagem);
  else avisar(mensagem, 'erro');
}

export async function desativarPonto(id) {
  const ponto = buscarPonto(id);
  const confirmou = await confirmarAcao({
    titulo: `Desativar ${ponto?.codigo || 'ponto'}?`,
    mensagem: 'O ponto sai do mapa e deixa de receber medições. O histórico é mantido e você pode reativar depois.',
    textoConfirmar: 'Desativar',
    perigo: true,
  });
  if (!confirmou) return;
  try {
    await api.desativarPonto(id);
    fecharDialogo({ forcar: true });
    avisar('Ponto desativado. O histórico foi mantido.', 'sucesso');
    mostrarAbaPontos();
  } catch (erro) {
    mostrarErroDoPonto(erro.message);
  }
}

export async function excluirPonto(id) {
  const ponto = buscarPonto(id);
  if (!ponto) return;
  limparErros(document.getElementById('form-ponto'));
  const confirmou = await confirmarAcao({
    titulo: `Excluir o ponto ${ponto.codigo}?`,
    mensagem: 'Só é possível excluir um ponto sem medições reais nem ocorrências; as medições simuladas dele também serão apagadas. Essa ação não pode ser desfeita.',
    textoConfirmar: 'Excluir ponto',
    perigo: true,
  });
  if (!confirmou) return;
  try {
    await api.excluirPonto(id);
    fecharDialogo({ forcar: true });
    avisar(`Ponto ${ponto.codigo} excluído.`, 'sucesso');
    mostrarAbaPontos();
  } catch (erro) {
    // Ex.: o ponto tem histórico real. A mensagem da API explica e sugere desativar.
    mostrarErroDoPonto(erro.message);
  }
}

export async function reativarPonto(id) {
  try {
    await api.alterarPonto(id, { ativo: true });
    fecharDialogo();
    avisar('Ponto reativado.', 'sucesso');
    mostrarAbaPontos();
  } catch (erro) {
    avisar(erro.message, 'erro');
  }
}

export async function gerarChaveSensor(id) {
  const ponto = buscarPonto(id);
  if (ponto?.possui_chave_sensor) {
    const confirmou = await confirmarAcao({
      titulo: 'Trocar a chave do sensor?',
      mensagem: 'A chave atual deixa de funcionar na hora. O sensor só volta a enviar medições depois de receber a chave nova.',
      textoConfirmar: 'Trocar chave',
      perigo: true,
    });
    if (!confirmou) return;
  }
  try {
    const resultado = await api.gerarChaveSensor(id);
    abrirDialogo({
      titulo: `Chave do sensor ${escaparHtml(resultado.codigo_ponto)}`,
      corpo: `
        <div class="barra-mensagem atencao" role="note"><span data-icone="atencao"></span><p>${escaparHtml(resultado.mensagem)}</p></div>
        <div class="campo">
          <label class="campo-rotulo" for="chave-sensor">Chave</label>
          <input class="entrada texto-mono" id="chave-sensor" readonly value="${escaparHtml(resultado.chave_sensor)}" onfocus="this.select()">
        </div>
        <p class="texto-pequeno texto-apagado">O sensor envia <code>POST /api/sensor/medicoes</code> com o cabeçalho <code>X-Chave-Sensor</code>.</p>`,
      rodape: `<button class="botao" type="button" onclick="copiarChaveSensor(this)"><span data-icone="chave"></span>Copiar chave</button>
        <button class="botao principal" type="button" data-fechar-dialogo>Concluir</button>`,
      aoFechar: () => mostrarAbaPontos(),
      fixo: true,
    });
  } catch (erro) {
    avisar(erro.message, 'erro');
  }
}

export async function copiarChaveSensor(botao) {
  const campo = document.getElementById('chave-sensor');
  if (!campo) return;
  try {
    await navigator.clipboard.writeText(campo.value);
    botao.textContent = 'Copiada';
  } catch {
    campo.select();
    avisar('Selecione a chave e copie com Ctrl+C.', 'informacao');
  }
}
