"""Formato dos dados que entram e saem da API (validação feita pelo Pydantic)."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


LIMITE_DISTANCIA = 999_999  # cabe em NUMERIC(8,2)
PADRAO_CODIGO = re.compile(r"[A-Za-z0-9_-]+")

Classificacao = Literal["amarelo", "laranja", "vermelho"]
OrigemMedicao = Literal["manual", "simulada"]


def _vazio_para_nulo(valor):
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


def conferir_criterios(atencao, alerta, critica) -> None:
    valores = (atencao, alerta, critica)
    if all(valor is None for valor in valores):
        return
    if any(valor is None for valor in valores):
        raise ValueError("Informe os três critérios (atenção, alerta e crítico) ou deixe os três vazios.")
    if not (atencao > alerta > critica > 0):
        raise ValueError(
            "Os critérios são distâncias: atenção > alerta > crítico > 0 (quanto menor a distância, mais perto a água está)."
        )


def conferir_faixa_valida(minima, maxima) -> None:
    if minima is not None and maxima is not None and minima >= maxima:
        raise ValueError("A distância mínima válida precisa ser menor que a máxima.")


# ---------- Autenticação ----------

class PedidoLogin(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=160)
    senha: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str):
        valor = valor.lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("Informe um e-mail válido.")
        return valor


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str


class RespostaLogin(BaseModel):
    token_acesso: str
    tipo_token: str = "bearer"  # tipo definido pelo padrão HTTP (cabeçalho "Authorization: Bearer")
    usuario: UsuarioSaida


# ---------- Rios ----------

class RioEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=2, max_length=120)
    observacoes: str | None = Field(default=None, max_length=1000)

    limpar_vazios = field_validator("observacoes", mode="before")(_vazio_para_nulo)


class RioSaida(BaseModel):
    id: int
    nome: str
    observacoes: str | None
    quantidade_pontos: int = 0


# ---------- Pontos ----------

class ConfiguracaoPonto(BaseModel):
    """Campos editáveis de um ponto."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    rio_id: int | None = None
    bairro: str | None = Field(default=None, max_length=120)
    descricao_local: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    distancia_atencao_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    distancia_alerta_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    distancia_critica_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    criterios_provisorios: bool | None = None
    justificativa_criterios: str | None = Field(default=None, max_length=1000)
    distancia_minima_valida_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    distancia_maxima_valida_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    salto_maximo_cm: float | None = Field(default=None, gt=0, lt=LIMITE_DISTANCIA)
    minutos_para_desatualizar: int | None = Field(default=None, ge=1, le=43_200)
    ativo: bool | None = None

    limpar_vazios = field_validator(
        "bairro", "descricao_local", "justificativa_criterios", mode="before"
    )(_vazio_para_nulo)


class NovoPonto(ConfiguracaoPonto):
    codigo: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=2, max_length=120)
    rio_id: int
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, valor: str):
        if not PADRAO_CODIGO.fullmatch(valor):
            raise ValueError("O código aceita apenas letras, números, hífen e sublinhado.")
        return valor.upper()

    @model_validator(mode="after")
    def validar_regras(self):
        conferir_criterios(self.distancia_atencao_cm, self.distancia_alerta_cm, self.distancia_critica_cm)
        conferir_faixa_valida(self.distancia_minima_valida_cm, self.distancia_maxima_valida_cm)
        return self


class AlteracaoPonto(ConfiguracaoPonto):
    pass


class EstadoPonto(BaseModel):
    """Situação de um ponto calculada com dados reais ou com dados simulados."""

    modo: str
    situacao: str
    classificacao: str | None
    distancia_cm: float | None
    medida_em: datetime | None
    validade: str | None
    motivo_validade: str | None
    desatualizado: bool
    ultima_recebida_invalida: bool
    ocorrencia: dict | None


class PontoSaida(BaseModel):
    id: int
    codigo: str
    nome: str
    rio_id: int | None
    rio_nome: str | None
    bairro: str | None
    descricao_local: str | None
    latitude: float
    longitude: float
    distancia_atencao_cm: float | None
    distancia_alerta_cm: float | None
    distancia_critica_cm: float | None
    criterios_provisorios: bool
    justificativa_criterios: str | None
    distancia_minima_valida_cm: float | None
    distancia_maxima_valida_cm: float | None
    salto_maximo_cm: float | None
    minutos_para_desatualizar: int
    possui_chave_sensor: bool
    ativo: bool
    estado_real: EstadoPonto
    estado_simulado: EstadoPonto


class PontoPublico(BaseModel):
    id: int
    codigo: str
    nome: str
    rio_nome: str | None
    bairro: str | None
    latitude: float
    longitude: float
    possui_criterios: bool
    criterios_provisorios: bool
    estado: EstadoPonto


class ChaveSensorSaida(BaseModel):
    codigo_ponto: str
    chave_sensor: str
    mensagem: str


# ---------- Medições ----------

class NovaMedicao(BaseModel):
    distancia_cm: float = Field(gt=-LIMITE_DISTANCIA, lt=LIMITE_DISTANCIA)
    medida_em: datetime | None = None
    origem: OrigemMedicao = "manual"


class MedicaoDoSensor(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    codigo_ponto: str = Field(min_length=1, max_length=50)
    distancia_cm: float = Field(gt=-LIMITE_DISTANCIA, lt=LIMITE_DISTANCIA)
    medida_em: datetime | None = None


class MedicaoSaida(BaseModel):
    id: int
    ponto_id: int
    distancia_cm: float
    unidade: str
    origem: str
    medida_em: datetime
    recebida_em: datetime
    validade: str
    motivo_validade: str | None
    referencia_cm: float | None
    classificacao: str | None
    registrada_por: str | None


class NovaSimulacao(BaseModel):
    cenario: Literal["subida", "descida", "oscilacao"]
    distancia_inicial_cm: float = Field(gt=0, lt=LIMITE_DISTANCIA)
    variacao_cm: float = Field(gt=0, lt=LIMITE_DISTANCIA)
    quantidade: int = Field(default=12, ge=2, le=200)
    intervalo_minutos: int = Field(default=10, ge=1, le=1440)


class SimulacaoSaida(BaseModel):
    criadas: int
    suspeitas: int
    invalidas: int
    medicoes: list[MedicaoSaida]


# ---------- Ocorrências ----------

class NovaOcorrencia(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    classificacao: Classificacao = "vermelho"
    motivo: str = Field(min_length=3, max_length=2000)


class OcorrenciaSaida(BaseModel):
    id: int
    ponto_id: int
    ponto_codigo: str
    ponto_nome: str
    classificacao: str
    motivo: str
    aberta_por: str
    aberta_em: datetime
    encerrada_em: datetime | None
    encerrada_por: str | None


# ---------- Auditoria ----------

class EventoAuditoriaSaida(BaseModel):
    id: int
    autor: str
    acao: str
    entidade: str
    detalhes: str | None
    criado_em: datetime
