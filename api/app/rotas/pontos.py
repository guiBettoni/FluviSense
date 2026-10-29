import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.dependencias import exigir_operador, ponto_ou_404
from app.esquemas import (
    AlteracaoPonto,
    ChaveSensorSaida,
    EstadoPonto,
    NovoPonto,
    PontoPublico,
    PontoSaida,
    RioEntrada,
    RioSaida,
    conferir_criterios,
    conferir_faixa_valida,
)
from app.modelos import Medicao, Ocorrencia, PontoMonitoramento, Rio, Usuario
from app.servicos import registrar_auditoria
from app.servicos.medicoes import ORIGENS_REAIS, ORIGENS_SIMULADAS, estado_do_ponto, possui_criterios


roteador = APIRouter(tags=["rios e pontos"])

CAMPOS_CRITERIOS = ("distancia_atencao_cm", "distancia_alerta_cm", "distancia_critica_cm")
CAMPOS_OBRIGATORIOS = ("nome", "rio_id", "latitude", "longitude", "criterios_provisorios", "minutos_para_desatualizar", "ativo")


def plural(quantidade: int, singular: str, forma_plural: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else forma_plural}"


def _numero(valor):
    return None if valor is None else float(valor)


def ponto_saida(sessao: Session, ponto: PontoMonitoramento) -> PontoSaida:
    return PontoSaida(
        id=ponto.id,
        codigo=ponto.codigo,
        nome=ponto.nome,
        rio_id=ponto.rio_id,
        rio_nome=ponto.rio.nome if ponto.rio else None,
        bairro=ponto.bairro,
        descricao_local=ponto.descricao_local,
        latitude=ponto.latitude,
        longitude=ponto.longitude,
        distancia_atencao_cm=_numero(ponto.distancia_atencao_cm),
        distancia_alerta_cm=_numero(ponto.distancia_alerta_cm),
        distancia_critica_cm=_numero(ponto.distancia_critica_cm),
        criterios_provisorios=ponto.criterios_provisorios,
        justificativa_criterios=ponto.justificativa_criterios,
        distancia_minima_valida_cm=_numero(ponto.distancia_minima_valida_cm),
        distancia_maxima_valida_cm=_numero(ponto.distancia_maxima_valida_cm),
        salto_maximo_cm=_numero(ponto.salto_maximo_cm),
        minutos_para_desatualizar=ponto.minutos_para_desatualizar,
        possui_chave_sensor=bool(ponto.hash_chave_sensor),
        ativo=ponto.ativo,
        estado_real=EstadoPonto(**estado_do_ponto(sessao, ponto, "real")),
        estado_simulado=EstadoPonto(**estado_do_ponto(sessao, ponto, "simulada")),
    )


def rio_ou_400(sessao: Session, rio_id: int) -> Rio:
    rio = sessao.get(Rio, rio_id)
    if not rio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rio não encontrado.")
    return rio


# ---------- Público ----------

@roteador.get("/publico/pontos", response_model=list[PontoPublico])
def pontos_publicos(sessao: Session = Depends(obter_sessao)):
    """Pontos ativos com a situação calculada só com dados reais. Sem dados simulados nem configuração interna."""
    pontos = sessao.scalars(
        select(PontoMonitoramento).where(PontoMonitoramento.ativo.is_(True)).order_by(PontoMonitoramento.nome)
    ).all()
    return [
        PontoPublico(
            id=ponto.id,
            codigo=ponto.codigo,
            nome=ponto.nome,
            rio_nome=ponto.rio.nome if ponto.rio else None,
            bairro=ponto.bairro,
            latitude=ponto.latitude,
            longitude=ponto.longitude,
            possui_criterios=possui_criterios(ponto),
            criterios_provisorios=ponto.criterios_provisorios,
            estado=EstadoPonto(**estado_do_ponto(sessao, ponto, "real")),
        )
        for ponto in pontos
    ]


@roteador.get("/rios", response_model=list[RioSaida])
def listar_rios(sessao: Session = Depends(obter_sessao)):
    linhas = sessao.execute(
        select(Rio, func.count(PontoMonitoramento.id))
        .outerjoin(PontoMonitoramento, PontoMonitoramento.rio_id == Rio.id)
        .group_by(Rio.id)
        .order_by(Rio.nome)
    ).all()
    return [RioSaida(id=rio.id, nome=rio.nome, observacoes=rio.observacoes, quantidade_pontos=quantidade) for rio, quantidade in linhas]


# ---------- Rios (operador) ----------

@roteador.post("/rios", response_model=RioSaida, status_code=status.HTTP_201_CREATED)
def criar_rio(dados: RioEntrada, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    if sessao.scalar(select(Rio).where(func.lower(Rio.nome) == dados.nome.lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um rio com esse nome.")
    rio = Rio(nome=dados.nome, observacoes=dados.observacoes)
    sessao.add(rio)
    sessao.flush()
    registrar_auditoria(sessao, operador.email, "RIO_CRIADO", f"rio:{rio.id}", {"nome": rio.nome})
    sessao.commit()
    return RioSaida(id=rio.id, nome=rio.nome, observacoes=rio.observacoes, quantidade_pontos=0)


@roteador.put("/rios/{rio_id}", response_model=RioSaida)
def alterar_rio(
    rio_id: int, dados: RioEntrada, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)
):
    rio = sessao.get(Rio, rio_id)
    if not rio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rio não encontrado.")
    repetido = sessao.scalar(select(Rio).where(func.lower(Rio.nome) == dados.nome.lower(), Rio.id != rio_id))
    if repetido:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um rio com esse nome.")
    antes = {"nome": rio.nome, "observacoes": rio.observacoes}
    rio.nome = dados.nome
    rio.observacoes = dados.observacoes
    registrar_auditoria(
        sessao, operador.email, "RIO_ATUALIZADO", f"rio:{rio.id}",
        {"antes": antes, "depois": {"nome": rio.nome, "observacoes": rio.observacoes}},
    )
    sessao.commit()
    quantidade = sessao.scalar(select(func.count(PontoMonitoramento.id)).where(PontoMonitoramento.rio_id == rio.id))
    return RioSaida(id=rio.id, nome=rio.nome, observacoes=rio.observacoes, quantidade_pontos=quantidade or 0)


@roteador.delete("/rios/{rio_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_rio(rio_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    """Exclui um rio que não tem nenhum ponto (ativo ou desativado) ligado a ele."""
    rio = sessao.get(Rio, rio_id)
    if not rio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rio não encontrado. Ele pode já ter sido excluído.")
    quantidade = sessao.scalar(select(func.count(PontoMonitoramento.id)).where(PontoMonitoramento.rio_id == rio.id)) or 0
    if quantidade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O rio {rio.nome} tem {plural(quantidade, 'ponto ligado', 'pontos ligados')} (contando os desativados). "
            "Mude o rio desses pontos ou exclua-os antes de excluir o rio.",
        )
    registrar_auditoria(sessao, operador.email, "RIO_EXCLUIDO", f"rio:{rio.id}", {"nome": rio.nome})
    sessao.delete(rio)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Pontos (operador) ----------

@roteador.get("/pontos", response_model=list[PontoSaida])
def listar_pontos(sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    pontos = sessao.scalars(
        select(PontoMonitoramento).order_by(PontoMonitoramento.ativo.desc(), PontoMonitoramento.nome)
    ).all()
    return [ponto_saida(sessao, ponto) for ponto in pontos]


@roteador.get("/pontos/{ponto_id}", response_model=PontoSaida)
def obter_ponto(ponto_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    return ponto_saida(sessao, ponto_ou_404(sessao, ponto_id))


@roteador.post("/pontos", response_model=PontoSaida, status_code=status.HTTP_201_CREATED)
def criar_ponto(dados: NovoPonto, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    if sessao.scalar(select(PontoMonitoramento).where(PontoMonitoramento.codigo == dados.codigo)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um ponto com esse código.")
    rio_ou_400(sessao, dados.rio_id)
    valores = dados.model_dump(exclude_none=True)
    valores.setdefault("criterios_provisorios", True)
    ponto = PontoMonitoramento(**valores)
    sessao.add(ponto)
    sessao.flush()
    registrar_auditoria(sessao, operador.email, "PONTO_CRIADO", ponto.codigo, {campo: valor for campo, valor in valores.items() if campo != "codigo"})
    sessao.commit()
    sessao.refresh(ponto)
    return ponto_saida(sessao, ponto)


@roteador.put("/pontos/{ponto_id}", response_model=PontoSaida)
def alterar_ponto(
    ponto_id: int, dados: AlteracaoPonto, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)
):
    ponto = ponto_ou_404(sessao, ponto_id)
    valores = dados.model_dump(exclude_unset=True)
    if not valores:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe ao menos um campo para atualizar.")
    for campo in CAMPOS_OBRIGATORIOS:
        if campo in valores and valores[campo] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"O campo {campo} não pode ficar vazio.")
    if "rio_id" in valores:
        rio_ou_400(sessao, valores["rio_id"])

    finais = {
        campo: valores.get(campo, _numero(getattr(ponto, campo)))
        for campo in (*CAMPOS_CRITERIOS, "distancia_minima_valida_cm", "distancia_maxima_valida_cm")
    }
    try:
        conferir_criterios(*(finais[campo] for campo in CAMPOS_CRITERIOS))
        conferir_faixa_valida(finais["distancia_minima_valida_cm"], finais["distancia_maxima_valida_cm"])
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from None

    mudancas = {}
    for campo, valor in valores.items():
        atual = getattr(ponto, campo)
        atual = _numero(atual) if campo.endswith("_cm") else atual
        if atual != valor:
            mudancas[campo] = {"antes": atual, "depois": valor}
            setattr(ponto, campo, valor)
    if not mudancas:
        return ponto_saida(sessao, ponto)
    ponto.atualizado_em = datetime.now(timezone.utc)
    acao = "CRITERIOS_ALTERADOS" if any(campo in mudancas for campo in CAMPOS_CRITERIOS) else "PONTO_ATUALIZADO"
    registrar_auditoria(sessao, operador.email, acao, ponto.codigo, mudancas)
    sessao.commit()
    sessao.refresh(ponto)
    return ponto_saida(sessao, ponto)


@roteador.delete("/pontos/{ponto_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_ponto(ponto_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    """Desativa o ponto. O histórico de medições nunca é apagado."""
    ponto = ponto_ou_404(sessao, ponto_id)
    if ponto.ativo:
        ponto.ativo = False
        ponto.atualizado_em = datetime.now(timezone.utc)
        registrar_auditoria(sessao, operador.email, "PONTO_DESATIVADO", ponto.codigo)
        sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@roteador.delete("/pontos/{ponto_id}/definitivo", status_code=status.HTTP_204_NO_CONTENT)
def excluir_ponto(ponto_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    """Exclui de vez um ponto sem histórico real (ex.: cadastrado por engano ou só usado em simulação).

    Ponto com medição real ou ocorrência não pode ser excluído, para preservar o histórico (RNF04):
    nesse caso o caminho é desativar.
    """
    ponto = ponto_ou_404(sessao, ponto_id)
    reais = sessao.scalar(
        select(func.count(Medicao.id)).where(Medicao.ponto_id == ponto.id, Medicao.origem.in_(ORIGENS_REAIS))
    ) or 0
    ocorrencias = sessao.scalar(select(func.count(Ocorrencia.id)).where(Ocorrencia.ponto_id == ponto.id)) or 0
    if reais or ocorrencias:
        partes = []
        if reais:
            partes.append(plural(reais, "medição real", "medições reais"))
        if ocorrencias:
            partes.append(plural(ocorrencias, "ocorrência", "ocorrências"))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O ponto {ponto.codigo} tem {' e '.join(partes)} no histórico e não pode ser excluído. "
            "Use Desativar: ele sai do mapa e o histórico é mantido.",
        )
    simuladas = sessao.execute(
        delete(Medicao).where(Medicao.ponto_id == ponto.id, Medicao.origem.in_(ORIGENS_SIMULADAS))
    ).rowcount
    registrar_auditoria(
        sessao, operador.email, "PONTO_EXCLUIDO", ponto.codigo, {"nome": ponto.nome, "medicoes_simuladas_apagadas": simuladas}
    )
    sessao.delete(ponto)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@roteador.post("/pontos/{ponto_id}/chave-sensor", response_model=ChaveSensorSaida)
def gerar_chave_sensor(ponto_id: int, sessao: Session = Depends(obter_sessao), operador: Usuario = Depends(exigir_operador)):
    """Gera (ou troca) a chave que um sensor usa para enviar medições reais deste ponto."""
    ponto = ponto_ou_404(sessao, ponto_id)
    chave = secrets.token_urlsafe(24)
    trocada = bool(ponto.hash_chave_sensor)
    ponto.hash_chave_sensor = hashlib.sha256(chave.encode("utf-8")).hexdigest()
    registrar_auditoria(sessao, operador.email, "CHAVE_DISPOSITIVO_TROCADA" if trocada else "CHAVE_DISPOSITIVO_GERADA", ponto.codigo)
    sessao.commit()
    return ChaveSensorSaida(
        codigo_ponto=ponto.codigo,
        chave_sensor=chave,
        mensagem="Guarde esta chave agora. Ela não será exibida novamente; a chave anterior deixou de valer.",
    )
