"""Mensagens de erro da API em português do Brasil.

O FastAPI e o Pydantic devolvem os erros de validação em inglês ("Field required",
"Input should be a valid number"). Este módulo troca essas mensagens por textos em português,
para que o operador veja a explicação certa na tela. As mensagens que o próprio projeto escreve
(por exemplo, nas regras de critérios) já estão em português e passam sem mudança.
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Nome do campo como o operador o enxerga na tela.
NOMES_DE_CAMPO = {
    "nome": "Nome",
    "observacoes": "Observações",
    "codigo": "Código",
    "email": "E-mail",
    "senha": "Senha",
    "rio_id": "Rio",
    "bairro": "Bairro",
    "descricao_local": "Descrição do local",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "distancia_atencao_cm": "Distância de atenção",
    "distancia_alerta_cm": "Distância de alerta",
    "distancia_critica_cm": "Distância crítica",
    "justificativa_criterios": "Origem ou justificativa dos critérios",
    "distancia_minima_valida_cm": "Distância mínima válida",
    "distancia_maxima_valida_cm": "Distância máxima válida",
    "salto_maximo_cm": "Salto máximo",
    "minutos_para_desatualizar": "Prazo para dado desatualizado",
    "distancia_cm": "Distância",
    "medida_em": "Horário da medição",
    "origem": "Origem",
    "codigo_ponto": "Código do ponto",
    "classificacao": "Classificação",
    "motivo": "Motivo",
    "cenario": "Cenário",
    "distancia_inicial_cm": "Distância inicial",
    "variacao_cm": "Variação total",
    "quantidade": "Quantidade de medições",
    "intervalo_minutos": "Intervalo entre medições",
    "modo": "Dados",
    "desde": "Desde",
    "ate": "Até",
    "limite": "Limite",
    "situacao": "Situação",
}

MENSAGENS_HTTP = {
    404: "Recurso não encontrado.",
    405: "Método não permitido para este endereço.",
    401: "Não autenticado.",
    403: "Acesso negado.",
    429: "Muitas requisições. Tente de novo em instantes.",
    500: "Erro interno do servidor.",
}

# Textos padrão em inglês que o FastAPI/Starlette usa quando o código não informa o motivo.
DETALHES_PADRAO_EM_INGLES = {
    "Not Found",
    "Method Not Allowed",
    "Not authenticated",
    "Forbidden",
    "Unauthorized",
    "Internal Server Error",
}


def _mensagem(erro: dict) -> str:
    tipo = erro.get("type", "")
    ctx = erro.get("ctx") or {}

    if tipo == "value_error":
        # Mensagem escrita pelo projeto, já em português: "Value error, <texto>".
        return str(erro.get("msg", "")).removeprefix("Value error, ")

    if tipo == "missing":
        texto = "Campo obrigatório."
    elif tipo in {"string_type", "string_pattern_mismatch"}:
        texto = "Informe um texto válido."
    elif tipo in {"int_parsing", "int_type", "int_from_float"}:
        texto = "Informe um número inteiro."
    elif tipo in {"float_parsing", "float_type", "decimal_parsing", "decimal_type"}:
        texto = "Informe um número válido."
    elif tipo == "string_too_short":
        texto = f"Texto curto demais (mínimo de {ctx.get('min_length')} caracteres)."
    elif tipo == "string_too_long":
        texto = f"Texto longo demais (máximo de {ctx.get('max_length')} caracteres)."
    elif tipo == "greater_than":
        texto = f"O valor precisa ser maior que {ctx.get('gt')}."
    elif tipo == "greater_than_equal":
        texto = f"O valor precisa ser maior ou igual a {ctx.get('ge')}."
    elif tipo == "less_than":
        texto = f"O valor precisa ser menor que {ctx.get('lt')}."
    elif tipo == "less_than_equal":
        texto = f"O valor precisa ser menor ou igual a {ctx.get('le')}."
    elif tipo in {"datetime_parsing", "datetime_type", "datetime_from_date_parsing"}:
        texto = "Data e hora inválidas. Use o formato 2026-10-21T14:30:00-03:00."
    elif tipo in {"bool_parsing", "bool_type"}:
        texto = "Informe verdadeiro ou falso."
    elif tipo == "json_invalid":
        return "O corpo da requisição não é um JSON válido."
    elif tipo in {"literal_error", "enum"}:
        texto = "Valor não permitido."
    elif tipo == "extra_forbidden":
        texto = "Campo não reconhecido."
    elif tipo in {"too_short", "too_long"}:
        texto = "Quantidade de itens fora do permitido."
    else:
        texto = "Valor inválido."

    campo = _campo(erro)
    if campo:
        return f"{NOMES_DE_CAMPO.get(campo, campo)}: {texto}"
    return texto


def _campo(erro: dict) -> str | None:
    localizacao = [parte for parte in erro.get("loc", ()) if parte not in {"body", "query", "path", "header"}]
    return localizacao[-1] if localizacao and isinstance(localizacao[-1], str) else None


def erro_de_validacao(requisicao: Request, erro_validacao: RequestValidationError) -> JSONResponse:
    """Resposta 422: {"detalhe": [{"campo": ..., "mensagem": ...}]}."""
    detalhes = [{"campo": _campo(erro), "mensagem": _mensagem(erro)} for erro in erro_validacao.errors()]
    return JSONResponse(status_code=422, content={"detalhe": detalhes})


def erro_http(requisicao: Request, erro: StarletteHTTPException) -> JSONResponse:
    """Demais erros: {"detalhe": "texto"}."""
    detalhe = erro.detail
    if not isinstance(detalhe, str) or detalhe in DETALHES_PADRAO_EM_INGLES:
        detalhe = MENSAGENS_HTTP.get(erro.status_code, "Não foi possível concluir a operação.")
    return JSONResponse(status_code=erro.status_code, content={"detalhe": detalhe}, headers=getattr(erro, "headers", None))
