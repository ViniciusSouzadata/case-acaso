"""Gera dist/entrega.pdf a partir de docs/entrega.md (T-605, rascunho).

Sem dependência nova: converte o subconjunto de Markdown usado no documento (títulos, parágrafos,
tabelas, **negrito** e `código`) com a biblioteca padrão e imprime com o Chrome/Edge já instalado
na máquina (--print-to-pdf). O texto do documento não é alterado; estilo e fontes ficam em scripts/pdf/.

Uso: python scripts/gerar_pdf.py [--saida dist/entrega.pdf]
Navegador: variável NAVEGADOR ou, se ausente, Chrome/Edge nos caminhos padrão do Windows e Linux.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "docs" / "entrega.md"
PASTA_PDF = Path(__file__).resolve().parent / "pdf"

CANDIDATOS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def achar_navegador() -> str:
    env = os.environ.get("NAVEGADOR")
    if env:
        return env
    for c in CANDIDATOS:
        if Path(c).exists() or shutil.which(c):
            return c
    raise SystemExit("Nenhum Chrome/Edge encontrado. Defina a variável NAVEGADOR com o caminho do executável.")


def inline(texto: str) -> str:
    """Escapa HTML e converte `código` e **negrito**."""
    partes = re.split(r"(`[^`]+`)", texto)
    saida = []
    for p in partes:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            saida.append(f"<code>{html.escape(p[1:-1])}</code>")
        else:
            e = html.escape(p, quote=False)
            saida.append(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e))
    return "".join(saida)


def celulas(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def tabela(linhas: list[str], classe: str = "") -> str:
    cab = celulas(linhas[0])
    alinh = []
    for c in celulas(linhas[1]):
        alinh.append(" dir" if c.endswith(":") and not c.startswith(":") else " cen" if c.startswith(":") and c.endswith(":") else "")
    def cls(i: int) -> str:
        return f' class="{alinh[i].strip()}"' if i < len(alinh) and alinh[i] else ""
    th = "".join(f"<th{cls(i)}>{inline(c)}</th>" for i, c in enumerate(cab))
    corpo = []
    for l in linhas[2:]:
        tds = "".join(f"<td{cls(i)}>{inline(c)}</td>" for i, c in enumerate(celulas(l)))
        corpo.append(f"<tr>{tds}</tr>")
    c = f' class="{classe}"' if classe else ""
    return f"<table{c}><thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table>"


def converter(md: str) -> str:
    linhas = md.splitlines()
    out: list[str] = []
    i = 0
    n_tabela = 0
    h2_vistos = 0
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1
        elif l.startswith("# "):
            titulo = inline(l[2:])
            autoria = ""
            j = i + 1
            while j < len(linhas) and not linhas[j].strip():
                j += 1
            if j < len(linhas) and not linhas[j].startswith(("#", "|")):
                autoria = f'<p class="autoria">{inline(linhas[j])}</p>'
                i = j
            out.append(f'<header class="capa"><h1>{titulo}</h1>{autoria}</header>')
            i += 1
        elif l.startswith("## "):
            h2_vistos += 1
            # a página 1 é o resumo; a primeira seção numerada começa em página nova
            nova = ' class="nova-pagina"' if l.startswith("## 1.") else ""
            out.append(f"<h2{nova}>{inline(l[3:])}</h2>")
            i += 1
        elif l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i])
                i += 1
            n_tabela += 1
            classe = "mapa" if n_tabela == 1 else "telas" if bloco[0].lstrip("| ").startswith("Tela ") else ""
            out.append(tabela(bloco, classe))
        else:
            par = []
            while i < len(linhas) and linhas[i].strip() and not linhas[i].startswith(("#", "|")):
                par.append(linhas[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(par))}</p>")
    return "\n".join(out)


def pagina_html(corpo: str) -> str:
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        "<title>O que faz uma pessoa voltar ao assistente em até 7 dias</title>"
        '<link rel="stylesheet" href="estilo.css"></head><body>' + corpo + "</body></html>"
    )


def contar_paginas(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf.read_bytes()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(RAIZ / "dist" / "entrega.pdf"))
    args = ap.parse_args()
    saida = Path(args.saida).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)

    corpo = converter(ENTRADA.read_text(encoding="utf-8"))
    # monta a página ao lado do CSS e das fontes, para os caminhos relativos funcionarem
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        shutil.copytree(PASTA_PDF / "fonts", tmp_p / "fonts")
        shutil.copy(PASTA_PDF / "estilo.css", tmp_p / "estilo.css")
        (tmp_p / "entrega.html").write_text(pagina_html(corpo), encoding="utf-8")
        perfil = tmp_p / "perfil"
        cmd = [
            achar_navegador(), "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={perfil}", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=5000", f"--print-to-pdf={saida}", (tmp_p / "entrega.html").as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not saida.exists() or saida.stat().st_size == 0:
        print("Falha ao gerar o PDF.", r.stderr[-400:], file=sys.stderr)
        return 1
    print(f"PDF: {saida}  ({contar_paginas(saida)} páginas, {saida.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
