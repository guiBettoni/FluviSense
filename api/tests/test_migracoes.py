import pytest
from sqlalchemy import inspect

from app.banco import Base, motor
from conftest import USANDO_POSTGRES


@pytest.mark.skipif(not USANDO_POSTGRES, reason="As migrações só rodam em PostgreSQL (defina TEST_DATABASE_URL).")
def test_migracoes_criam_todas_as_colunas_usadas_pelos_modelos():
    inspetor = inspect(motor)
    for tabela in Base.metadata.sorted_tables:
        colunas = {coluna["name"] for coluna in inspetor.get_columns(tabela.name)}
        esperado = {coluna.name for coluna in tabela.columns}
        assert esperado <= colunas, f"{tabela.name}: faltam {esperado - colunas}"


@pytest.mark.skipif(not USANDO_POSTGRES, reason="As migrações só rodam em PostgreSQL (defina TEST_DATABASE_URL).")
def test_banco_nao_tem_mais_nomes_em_ingles():
    """Depois da migração 006, nenhuma tabela, coluna, restrição, índice ou sequência fica com nome em inglês."""
    # Palavras em inglês que apareciam nos nomes antigos. A comparação é feita por parte do nome
    # (separada por "_"), para não confundir com palavras em português como "valida".
    palavras_antigas = {
        "river", "rivers", "monitoring", "point", "points", "measurement", "measurements", "measured", "occurrence",
        "occurrences", "app", "users", "audit", "events", "readings", "residents", "shelters", "schema", "migrations",
        "name", "code", "active", "created", "updated", "distance", "valid", "min", "max", "jump", "stale", "after",
        "minutes", "reason", "origin", "unit", "role", "password", "status", "threshold", "pkey", "fkey", "key",
        "check", "single", "operator", "opened", "closed", "received", "reference", "classification", "validity",
        "criteria", "note", "provisional", "device", "level", "water", "street", "consent", "capacity", "occupancy",
    }
    with motor.connect() as conexao:
        nomes = [linha[0] for linha in conexao.exec_driver_sql(
            "select table_name from information_schema.tables where table_schema = 'public' "
            "union all select column_name from information_schema.columns where table_schema = 'public' "
            "union all select conname from pg_constraint where connamespace = 'public'::regnamespace "
            "union all select indexname from pg_indexes where schemaname = 'public' "
            "union all select sequencename from pg_sequences where schemaname = 'public'"
        )]
    em_ingles = sorted(nome for nome in set(nomes) if set(nome.split("_")) & palavras_antigas)
    assert em_ingles == []
