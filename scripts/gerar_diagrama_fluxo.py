"""Gera docs/arquitetura/fluxo-bruto-tela.png (fluxo do arquivo bruto até as 3 telas).

Só usa matplotlib. Uso: PYTHONUTF8=1 .venv/Scripts/python.exe scripts/gerar_diagrama_fluxo.py
Os nomes das telas são os de app/mensagens/pt.json (chave "nav").
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "arquitetura" / "fluxo-bruto-tela.png"


def nomes_das_telas() -> list[str]:
    nav = json.loads((RAIZ / "app" / "mensagens" / "pt.json").read_text(encoding="utf-8"))["nav"]
    return [nav["retencao"], nav["fatores"], nav["dados"]]


def caixa(ax, x, y, w, h, texto, cor="#ffffff", borda="#4c3a9e"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=cor, ec=borda, lw=1.6))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=8.8, color="#1b1b2f")


def seta(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color="#1b1b2f", lw=1.5, shrinkA=0, shrinkB=0))


def main() -> None:
    telas = nomes_das_telas()
    fig, ax = plt.subplots(figsize=(18, 5.4), dpi=110)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    caixa(ax, 0.1, 2.0, 2.2, 1.2, "WildChat-1M, Brasil\ndata/bruto/*.parquet")
    caixa(ax, 2.9, 2.0, 2.4, 1.2, "Carga (Python)\nmigra · verifica · carrega")
    caixa(ax, 5.9, 2.0, 1.6, 1.2, "Postgres 16", cor="#efeaff")
    caixa(ax, 2.9, 0.2, 2.8, 1.3, "ops.*\nlotes · rejeitados ·\nreconciliação · parâmetros")
    caixa(ax, 8.1, 2.0, 1.8, 1.2, "stg.*\n(bruto tratado)")
    caixa(ax, 10.5, 3.8, 2.2, 1.0, "mart.*\n(tabelas de negócio)")
    caixa(ax, 10.5, 0.6, 2.6, 1.5, "Análise (Python)\nefeitos · margem de erro\nFDR · decomposição")
    caixa(ax, 13.7, 0.8, 1.6, 0.9, "resultado.*")
    caixa(ax, 13.4, 2.3, 2.0, 1.4, "API (Next.js)\npapel app_ro,\nsó leitura", cor="#efeaff")
    caixa(ax, 15.9, 1.3, 2.0, 2.6, "Telas\n\n" + "\n".join(telas), cor="#efeaff")

    seta(ax, 2.3, 2.6, 2.9, 2.6)
    seta(ax, 5.3, 2.6, 5.9, 2.6)
    seta(ax, 4.1, 2.0, 4.1, 1.5)
    seta(ax, 7.5, 2.6, 8.1, 2.6)
    seta(ax, 9.9, 2.9, 10.5, 4.3)
    seta(ax, 9.9, 2.3, 10.5, 1.6)
    seta(ax, 12.7, 4.3, 14.0, 3.7)
    seta(ax, 13.1, 1.25, 13.7, 1.25)
    seta(ax, 14.5, 1.7, 14.5, 2.3)
    seta(ax, 15.4, 3.0, 15.9, 3.0)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAIDA, bbox_inches="tight", facecolor="white")
    print(f"gerado: {SAIDA}")


if __name__ == "__main__":
    main()
