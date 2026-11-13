"""Gera dist/case_acaso.zip a partir do `git archive` de uma referência (padrão: main).

Só entra o que está versionado no git. Depois de gerar, confere que nada proibido
(segredo, dados brutos pesados, ambiente, cache) foi para dentro e lista o conteúdo por pasta.

Uso: python scripts/empacotar.py [--ref main] [--saida dist/case_acaso.zip]
Regerar depois de uma mudança: faça o commit e rode o mesmo comando.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Prefixos/segmentos que não podem aparecer no zip.
PROIBIDOS_PREFIXO = ("data/raw/", "data/interim/", ".venv/", "dist/")
PROIBIDOS_SEGMENTO = ("node_modules", ".next", "__pycache__", ".git")
OBRIGATORIOS = ("README.md", "docker-compose.yml", "data/bruto/wildchat_brasil.parquet")


def violacoes(nomes: list[str]) -> list[str]:
    """Lista os caminhos proibidos presentes (funcao pura, testavel)."""
    ruins: list[str] = []
    for n in nomes:
        partes = n.split("/")
        base = partes[-1]
        if n.startswith(PROIBIDOS_PREFIXO) or any(p in PROIBIDOS_SEGMENTO for p in partes):
            ruins.append(n)
        elif base == ".env" or (base.startswith(".env.") and base != ".env.example"):
            ruins.append(n)
        elif base.startswith("validacao_manual_") and base.endswith(".csv"):
            ruins.append(n)  # planilhas com texto de conversa
    return ruins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main")
    ap.add_argument("--saida", default="dist/case_acaso.zip")
    a = ap.parse_args()

    saida = (RAIZ / a.saida).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "archive", "--format=zip", "--prefix=case_acaso/", "-o", str(saida), a.ref],
        cwd=RAIZ, check=True,
    )

    with zipfile.ZipFile(saida) as z:
        info = [i for i in z.infolist() if not i.is_dir()]
    nomes = [i.filename.removeprefix("case_acaso/") for i in info]

    ruins = violacoes(nomes)
    faltam = [o for o in OBRIGATORIOS if o not in nomes]
    por_pasta: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for i, n in zip(info, nomes):
        pasta = n.split("/")[0] if "/" in n else "(raiz)"
        por_pasta[pasta][0] += 1
        por_pasta[pasta][1] += i.compress_size

    print(f"ref: {a.ref} ({subprocess.check_output(['git', 'rev-parse', '--short', a.ref], cwd=RAIZ, text=True).strip()})")
    for pasta, (qtd, tam) in sorted(por_pasta.items()):
        print(f"  {pasta:<14} {qtd:>5} arquivos  {tam / 1e6:>8.2f} MB (comprimido)")
    print(f"total: {len(nomes)} arquivos, zip = {saida.stat().st_size / 1e6:.2f} MB -> {saida}")
    if ruins or faltam:
        print("ERRO: proibidos no zip:", ruins, "| faltando:", faltam, file=sys.stderr)
        saida.unlink()
        return 1
    print("conferencia OK: sem .env, data/raw, data/interim, .venv, node_modules, cache; data/bruto incluido")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
