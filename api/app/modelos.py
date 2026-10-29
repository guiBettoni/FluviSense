"""Tabelas usadas pela aplicação.

As tabelas do MVP de 2026.1 (sensores, leituras_sensores, moradores, abrigos, ocorrencias_manuais)
continuam no banco como registro, mas não são usadas pelo código.
Ver documentos/tecnico/03-arquitetura-e-dados.md.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.banco import Base


class Rio(Base):
    __tablename__ = "rios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    pontos: Mapped[list["PontoMonitoramento"]] = relationship(back_populates="rio")


class PontoMonitoramento(Base):
    """Ponto de monitoramento. Cada ponto tem um único sensor (ver decisão D3)."""

    __tablename__ = "pontos_monitoramento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    rio_id: Mapped[int | None] = mapped_column(ForeignKey("rios.id"))
    bairro: Mapped[str | None] = mapped_column(String(120))
    descricao_local: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Critérios de classificação em distância (cm). Quanto menor a distância, mais perto a água está do sensor.
    distancia_atencao_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    distancia_alerta_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    distancia_critica_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    criterios_provisorios: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    justificativa_criterios: Mapped[str | None] = mapped_column(Text)

    # Parâmetros técnicos de validação das medições.
    distancia_minima_valida_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    distancia_maxima_valida_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    salto_maximo_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    minutos_para_desatualizar: Mapped[int] = mapped_column(Integer, nullable=False, default=720)

    hash_chave_sensor: Mapped[str | None] = mapped_column(String(64))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rio: Mapped[Rio | None] = relationship(back_populates="pontos")


class Medicao(Base):
    __tablename__ = "medicoes"
    __table_args__ = (Index("medicoes_ponto_medida_idx", "ponto_id", "medida_em"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ponto_id: Mapped[int] = mapped_column(ForeignKey("pontos_monitoramento.id"), nullable=False)
    distancia_cm: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False, default="cm")
    origem: Mapped[str] = mapped_column(String(20), nullable=False)  # sensor | manual | simulada
    medida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recebida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    validade: Mapped[str] = mapped_column(String(20), nullable=False)  # valida | suspeita | invalida
    motivo_validade: Mapped[str | None] = mapped_column(String(255))
    referencia_cm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    classificacao: Mapped[str | None] = mapped_column(String(20))
    registrada_por: Mapped[str | None] = mapped_column(String(160))


class Ocorrencia(Base):
    __tablename__ = "ocorrencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ponto_id: Mapped[int] = mapped_column(ForeignKey("pontos_monitoramento.id"), nullable=False, index=True)
    classificacao: Mapped[str] = mapped_column(String(20), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    aberta_por: Mapped[str] = mapped_column(String(160), nullable=False)
    aberta_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    encerrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    encerrada_por: Mapped[str | None] = mapped_column(String(160))


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    hash_senha: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False, default="OPERADOR")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EventoAuditoria(Base):
    __tablename__ = "eventos_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    autor: Mapped[str] = mapped_column(String(120), nullable=False)
    acao: Mapped[str] = mapped_column(String(120), nullable=False)
    entidade: Mapped[str] = mapped_column(String(120), nullable=False)
    detalhes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
