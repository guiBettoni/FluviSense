"""Cria o operador do FluviSense (só existe um operador ativo; ver migração 002).

Uso (a partir da pasta api, com DATABASE_URL configurada):
    python scripts/criar_operador.py --email operador@exemplo.com --nome "Nome"
    python scripts/criar_operador.py --email operador@exemplo.com --mostrar-sql   # só imprime o INSERT

A senha é pedida no terminal. Em automação, pode vir da variável FLUVISENSE_OPERATOR_PASSWORD.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path


PASTA_API = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA_API))

from app.seguranca import gerar_hash_senha  # noqa: E402


def texto_sql(valor: str) -> str:
    return "'" + valor.replace("'", "''") + "'"


def ler_senha() -> str:
    senha = os.getenv("FLUVISENSE_OPERATOR_PASSWORD")
    if senha is None:
        senha = getpass.getpass("Senha do operador: ")
        if senha != getpass.getpass("Confirme a senha: "):
            raise SystemExit("As senhas não conferem.")
    if len(senha) < 8:
        raise SystemExit("Use uma senha com pelo menos 8 caracteres.")
    return senha


def executar() -> None:
    analisador = argparse.ArgumentParser(description="Cria o operador único do FluviSense.")
    analisador.add_argument("--email", required=True)
    analisador.add_argument("--nome", default="Operador FluviSense")
    analisador.add_argument("--mostrar-sql", action="store_true", help="Só imprime o SQL, sem gravar no banco.")
    argumentos = analisador.parse_args()

    email = argumentos.email.strip().lower()
    nome = argumentos.nome.strip()
    hash_senha = gerar_hash_senha(ler_senha())

    if argumentos.mostrar_sql:
        print(
            "insert into public.usuarios (nome, email, hash_senha, perfil, ativo)\n"
            f"values ({texto_sql(nome)}, {texto_sql(email)}, {texto_sql(hash_senha)}, 'OPERADOR', true);"
        )
        return

    from sqlalchemy import func, select

    from app.banco import SessaoLocal
    from app.modelos import Usuario

    with SessaoLocal() as sessao:
        if sessao.scalar(select(Usuario).where(func.lower(Usuario.email) == email)):
            raise SystemExit("Já existe um usuário com esse e-mail.")
        if sessao.scalar(select(Usuario).where(Usuario.perfil == "OPERADOR", Usuario.ativo.is_(True))):
            raise SystemExit("Já existe um operador ativo. Desative-o no banco antes de criar outro.")
        sessao.add(Usuario(nome=nome, email=email, hash_senha=hash_senha, perfil="OPERADOR", ativo=True))
        sessao.commit()
    print(f"Operador {email} criado.")


if __name__ == "__main__":
    executar()
