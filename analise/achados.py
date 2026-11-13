"""T-209: grava `seeds/achados.yaml` em `resultado.achado` (rascunho redigido a partir dos números de resultado.*)."""
from __future__ import annotations

from pathlib import Path

import psycopg
import yaml

from analise.gravar import substituir

ARQUIVO = Path(__file__).resolve().parent.parent / "seeds" / "achados.yaml"
COLUNAS = ["ordem", "titulo", "evidencia", "decisao", "limite"]
# opcionais (migração 012): número grande, rótulo e ação curta do cartão da Tela 2; ausentes viram NULL
OPCIONAIS = ["numero_destaque", "rotulo_destaque", "acao_curta"]


def ler(caminho: Path = ARQUIVO) -> list[dict]:
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    for a in dados:
        faltam = [c for c in COLUNAS if not str(a.get(c, "")).strip()]
        if faltam:
            raise ValueError(f"achado {a.get('ordem')}: campos vazios {faltam}")
    if sorted(a["ordem"] for a in dados) != list(range(1, len(dados) + 1)):
        raise ValueError("a ordem dos achados deve ser 1..n sem buracos")
    return dados


def gravar(conn: psycopg.Connection, caminho: Path = ARQUIVO) -> list[dict]:
    dados = ler(caminho)
    substituir(conn, "achado", COLUNAS + OPCIONAIS, [[a[c] for c in COLUNAS] + [(str(a[c]).strip() or None) if a.get(c) is not None else None for c in OPCIONAIS] for a in dados])
    return dados
