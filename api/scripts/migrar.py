"""Aplica as migrações SQL de api/migrations em ordem.

Uso (a partir da pasta api):
    python scripts/migrar.py              # aplica as pendentes
    python scripts/migrar.py --situacao   # só mostra o que já foi aplicado

Cada arquivo aplicado fica registrado na tabela migracoes_aplicadas. As migrações 001 a 003 usam
"if not exists"/"drop ... if exists", então rodar em um banco que já tinha essas tabelas é seguro.
"""

import argparse
import sys
from pathlib import Path


PASTA_API = Path(__file__).resolve().parents[1]
PASTA_MIGRACOES = PASTA_API / "migrations"
sys.path.insert(0, str(PASTA_API))

from app.banco import motor  # noqa: E402


# Até 28/10/2026 o registro se chamava schema_migrations e os arquivos tinham nomes em inglês.
# Bancos criados antes disso (como o do Supabase) são ajustados na primeira execução.
NOMES_ANTIGOS = {
    "001_base_schema": "001_esquema_base",
    "002_operator_auth": "002_autenticacao_operador",
    "003_positive_sensor_thresholds": "003_limiares_positivos_sensores",
    "005_row_level_security": "005_seguranca_por_linha",
}


def arquivos_de_migracao() -> list[Path]:
    return sorted(caminho for caminho in PASTA_MIGRACOES.glob("*.sql") if caminho.name[:3].isdigit())


def ajustar_registro_antigo(cursor) -> None:
    cursor.execute("select to_regclass('public.schema_migrations') is not null, to_regclass('public.migracoes_aplicadas') is not null")
    tem_antigo, tem_novo = cursor.fetchone()
    if not tem_antigo or tem_novo:
        return
    print("Ajustando o registro de migrações para os nomes em português...")
    cursor.execute("alter table public.schema_migrations rename to migracoes_aplicadas")
    cursor.execute("alter table public.migracoes_aplicadas rename column version to versao")
    cursor.execute("alter table public.migracoes_aplicadas rename column applied_at to aplicada_em")
    for antigo, novo in NOMES_ANTIGOS.items():
        cursor.execute("update public.migracoes_aplicadas set versao = %s where versao = %s", (novo, antigo))


def executar() -> None:
    analisador = argparse.ArgumentParser(description="Aplica as migrações do FluviSense.")
    analisador.add_argument("--situacao", action="store_true", help="Lista as migrações e não aplica nada.")
    argumentos = analisador.parse_args()

    if motor.dialect.name != "postgresql":
        raise SystemExit("As migrações são escritas para PostgreSQL. Confira DATABASE_URL.")

    conexao = motor.raw_connection()
    try:
        conexao.autocommit = True
        cursor = conexao.cursor()
        ajustar_registro_antigo(cursor)
        cursor.execute(
            "create table if not exists public.migracoes_aplicadas ("
            " versao varchar(120) primary key, aplicada_em timestamptz not null default now())"
        )
        cursor.execute("select versao from public.migracoes_aplicadas")
        aplicadas = {linha[0] for linha in cursor.fetchall()}

        pendentes = [caminho for caminho in arquivos_de_migracao() if caminho.stem not in aplicadas]
        for caminho in arquivos_de_migracao():
            marca = "aplicada" if caminho.stem in aplicadas else "pendente"
            print(f"{marca:9} {caminho.name}")
        if argumentos.situacao or not pendentes:
            if not pendentes:
                print("Nenhuma migração pendente.")
            return

        for caminho in pendentes:
            print(f"Aplicando {caminho.name}...")
            try:
                cursor.execute(caminho.read_text(encoding="utf-8"))
            except Exception as erro:
                cursor.execute("rollback")
                raise SystemExit(f"Falha em {caminho.name}: {erro}") from None
            cursor.execute("insert into public.migracoes_aplicadas (versao) values (%s)", (caminho.stem,))
        print("Migrações aplicadas.")
    finally:
        conexao.close()


if __name__ == "__main__":
    executar()
