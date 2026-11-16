"""Gera dist/case_acaso.zip a partir do `git archive` de uma referência (padrão: main).

Só entra o que está versionado no git. Depois de gerar, confere que nada proibido
(segredo, dados brutos pesados, ambiente, cache) foi para dentro e lista o conteúdo por pasta.

Uso: python scripts/empacotar.py [--ref main] [--saida dist/case_acaso.zip]
Modo repositório (zip = repositório git com histórico, já sem os INTERNOS em todos os commits):
     python scripts/empacotar.py --repositorio <pasta do clone limpo> [--saida dist/case_acaso.zip]
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
# Notas internas de planejamento: ficam no git, mas não vão na entrega.
INTERNOS = (
    ".specs/project/STATE.md", ".specs/project/STATE-app.md",
    ".specs/project/PLANEJADOR-NOTAS.md", ".specs/project/HANDOFF.md",
)
OBRIGATORIOS = ("README.md", "docker-compose.yml", "data/bruto/wildchat_brasil.parquet", "docs/entrega.pdf", ".env.example")


def violacoes(nomes: list[str]) -> list[str]:
    """Lista os caminhos proibidos presentes (funcao pura, testavel)."""
    ruins: list[str] = []
    for n in nomes:
        partes = n.split("/")
        base = partes[-1]
        if n in INTERNOS or n.startswith(PROIBIDOS_PREFIXO) or any(p in PROIBIDOS_SEGMENTO for p in partes):
            ruins.append(n)
        elif base == ".env" or (base.startswith(".env.") and base != ".env.example"):
            ruins.append(n)
        elif base.startswith("validacao_manual_") and base.endswith(".csv"):
            ruins.append(n)  # planilhas com texto de conversa
    return ruins


def _git(pasta: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=pasta, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def empacotar_repositorio(clone: Path, saida: Path) -> int:
    """case_acaso/ = arquivos versionados do clone + a pasta .git (histórico). Confere INTERNOS em todo o histórico."""
    clone = clone.resolve()
    if _git(clone, "status", "--porcelain").strip():
        print("ERRO: o clone não está limpo (git status).", file=sys.stderr)
        return 1
    historico = {l for l in _git(clone, "log", "--all", "--name-only", "--format=").splitlines() if l}
    nos_commits = sorted(historico & set(INTERNOS))
    modos = {}
    for l in _git(clone, "ls-files", "-s").splitlines():
        meta, nome = l.split("	", 1)
        modos[nome] = 0o755 if meta.split()[0] == "100755" else 0o644
    nomes = sorted(modos)
    ruins = violacoes(nomes)
    faltam = [o for o in OBRIGATORIOS if o not in nomes]
    if ruins or faltam or nos_commits:
        print("ERRO: proibidos:", ruins, "| faltando:", faltam, "| INTERNOS no histórico:", nos_commits, file=sys.stderr)
        return 1
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.unlink(missing_ok=True)
    n_git = 0
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        def colocar(arq: Path, destino: str, modo: int) -> None:
            zi = zipfile.ZipInfo.from_file(arq, destino)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = (0o100000 | modo) << 16
            with open(arq, "rb") as f:
                z.writestr(zi, f.read())
        for n in nomes:
            colocar(clone / n, f"case_acaso/{n}", modos[n])
        for arq in sorted((clone / ".git").rglob("*")):
            if arq.is_file():
                colocar(arq, "case_acaso/" + arq.relative_to(clone).as_posix(), 0o644)
                n_git += 1
    commits = _git(clone, "rev-list", "--count", "--all").strip()
    print(f"clone: {clone} (HEAD {_git(clone, 'rev-parse', '--short', 'HEAD').strip()}, {commits} commits)")
    print(f"total: {len(nomes)} arquivos + {n_git} em .git, zip = {saida.stat().st_size / 1e6:.2f} MB -> {saida}")
    print("conferencia OK: sem INTERNOS em nenhum commit, sem .env, data/raw, cache; data/bruto incluido")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main")
    ap.add_argument("--repositorio", default=None, help="pasta do clone limpo: gera o zip com o histórico (.git)")
    ap.add_argument("--saida", default="dist/case_acaso.zip")
    a = ap.parse_args()

    saida = (RAIZ / a.saida).resolve()
    if a.repositorio:
        return empacotar_repositorio(Path(a.repositorio), saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "archive", "--format=zip", "--prefix=case_acaso/", "-o", str(saida), a.ref, "--", ".", *[f":(exclude){i}" for i in INTERNOS]],
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
