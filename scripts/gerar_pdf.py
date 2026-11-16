"""Gera dist/entrega.pdf a partir de docs/entrega.md (T-605, rascunho).

Sem dependência nova: converte o subconjunto de Markdown usado no documento (títulos, parágrafos,
tabelas, **negrito** e `código`) com a biblioteca padrão e imprime com o Chrome/Edge já instalado
na máquina (--print-to-pdf). O texto do documento não é alterado; estilo e fontes ficam em scripts/pdf/.

Uso: python scripts/gerar_pdf.py [--saida dist/entrega.pdf]
Navegador: variável NAVEGADOR ou, se ausente, Chrome/Edge nos caminhos padrão do Windows e Linux.
"""
from __future__ import annotations

import argparse
import base64
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
        alinh.append("dir" if c.endswith(":") and not c.startswith(":") else "cen" if c.startswith(":") and c.endswith(":") else "")

    def cls(i: int) -> str:
        return f' class="{alinh[i]}"' if i < len(alinh) and alinh[i] else ""

    th = "".join(f"<th{cls(i)}>{inline(c)}</th>" for i, c in enumerate(cab))
    corpo = []
    for l in linhas[2:]:
        tds = "".join(f"<td{cls(i)}>{inline(c)}</td>" for i, c in enumerate(celulas(l)))
        corpo.append(f"<tr>{tds}</tr>")
    c = f' class="{classe}"' if classe else ""
    return f"<table{c}><thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table>"


def cartoes(linhas: list[str]) -> str:
    """Tabela Número | O que é | Base vira cartões de indicador. O cartão do efeito real (−16) leva o laranja."""
    saida = []
    for l in linhas[2:]:
        num, que, base = (celulas(l) + ["", "", ""])[:3]
        num_txt = num.replace("**", "")
        destaque = " real" if num_txt.startswith(("−16", "-16")) else ""
        saida.append(
            f'<div class="indicador{destaque}"><div class="num">{html.escape(num_txt)}</div>'
            f'<div class="que">{inline(que)}</div><div class="base">{inline(base)}</div></div>'
        )
    return f'<div class="indicadores">{"".join(saida)}</div>'


def imagem_dados(caminho: str) -> str:
    arq = (RAIZ / "docs" / caminho).resolve()
    if not arq.exists():
        raise SystemExit(f"Imagem não encontrada: {arq}")
    return "data:image/png;base64," + base64.b64encode(arq.read_bytes()).decode()


def legenda(alt: str, telas: bool) -> str:
    if telas and ": " in alt:
        antes, depois = alt.split(": ", 1)
        return f'<strong class="cap">{inline(antes)}:</strong> {inline(depois)}'
    return inline(alt)


def grade(imgs: list[tuple[str, str]]) -> str:
    telas = "capturas" in imgs[0][1]
    cartoes_img = "".join(
        f'<figure class="cartao-img"><div class="moldura"><img src="{imagem_dados(c)}" alt="{html.escape(a)}"></div>'
        f'<figcaption>{legenda(a, telas)}</figcaption></figure>'
        for a, c in imgs
    )
    classe = "telas-img" if telas else "figuras-img"
    return f'<div class="grade {classe}">{cartoes_img}</div>'


def codigo(bloco: list[str]) -> str:
    """Bloco de código; comentário final '# antes' / '# depois' vai alinhado à direita, sem quebrar a linha."""
    linhas = []
    for l in bloco:
        m = re.match(r"^(.*?)\s+(#\s*\S.*)$", l)
        cod, com = (m.group(1), m.group(2)) if m else (l, "")
        linhas.append(f'<div class="lin"><span class="cod">{html.escape(cod)}</span><span class="com">{html.escape(com)}</span></div>')
    return f'<div class="codigo">{"".join(linhas)}</div>'


def fluxo(texto: str) -> str:
    passos = [p.strip() for p in " ".join(texto.split()).split(" -> ")]
    caixas = []
    for k, p in enumerate(passos):
        ultimo = " ultimo" if k == len(passos) - 1 else ""
        caixas.append(f'<div class="passo{ultimo}">{inline(p)}</div>')
        if k < len(passos) - 1:
            caixas.append('<div class="seta">&#8594;</div>')
    return f'<div class="fluxo">{"".join(caixas)}</div>'


RE_IMG = re.compile(r"^!\[(.*)\]\((.+)\)\s*$")


def converter(md: str) -> str:
    linhas = md.splitlines()
    out: list[str] = []
    i = 0
    secao = ""
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1
        elif l.startswith("```"):
            tipo = l[3:].strip()
            i += 1
            bloco = []
            while i < len(linhas) and not linhas[i].startswith("```"):
                bloco.append(linhas[i])
                i += 1
            i += 1
            if tipo == "fluxo":
                out.append(fluxo(" ".join(bloco)))
            else:
                out.append(codigo(bloco))
        elif l.startswith("# "):
            titulo = inline(l[2:])
            autoria = ""
            j = i + 1
            while j < len(linhas) and not linhas[j].strip():
                j += 1
            if j < len(linhas) and not linhas[j].startswith(("#", "|", ">", "-", "!", "`")):
                autoria = f'<p class="autoria">{inline(linhas[j])}</p>'
                i = j
            out.append(f'<header class="capa"><h1>{titulo}</h1>{autoria}</header>')
            i += 1
        elif l.startswith("## "):
            t = l[3:]
            secao = t
            m = re.match(r"(\d+)\.\s+(.*)", t)
            nova = ""
            if m:
                out.append(f'<h2{nova}><span class="selo">{m.group(1)}</span>{inline(m.group(2))}</h2>')
            else:
                out.append(f"<h2{nova}>{inline(t)}</h2>")
            i += 1
        elif l.startswith("> "):
            par = []
            while i < len(linhas) and linhas[i].startswith("> "):
                par.append(linhas[i][2:].strip())
                i += 1
            out.append(f'<div class="resposta">{inline(" ".join(par))}</div>')
        elif l.startswith("- "):
            itens = []
            while i < len(linhas) and linhas[i].startswith("- "):
                itens.append(f"<li>{inline(linhas[i][2:].strip())}</li>")
                i += 1
            out.append(f'<ul>{"".join(itens)}</ul>')
        elif RE_IMG.match(l):
            imgs = []
            while i < len(linhas) and RE_IMG.match(linhas[i]):
                m = RE_IMG.match(linhas[i])
                imgs.append((m.group(1), m.group(2)))
                i += 1
            out.append(grade(imgs))
        elif l.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i])
                i += 1
            cab = celulas(bloco[0])
            if cab[:3] == ["Número", "O que é", "Base"]:
                out.append(cartoes(bloco))
            else:
                out.append(tabela(bloco, "telas" if cab[0] == "Tela" else "achados" if cab[0] == "Achado" else ""))
        else:
            par = []
            while i < len(linhas) and linhas[i].strip() and not linhas[i].startswith(("#", "|", ">", "- ", "```", "![")):
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
