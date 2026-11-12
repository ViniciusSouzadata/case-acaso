"""Invariantes depois de trocar o seed de tema/recusa pelo do LLM: só o rótulo muda, a população e o número oficial não.

Parte 1 (arquivo, sem banco): o seed só tem ids, rótulos e origem; nada de texto de conversa.
Parte 2 (banco real, só leitura; pulada se não houver banco com a base real): 566/2.372 e reconciliação 9/9.
"""
import csv
import os
from pathlib import Path

import pytest

SEED = Path(__file__).resolve().parent.parent / "seeds" / "tema_conversa.csv"
COLUNAS = ["conversa_id", "tema", "tema_origem", "versao_prompt", "recusa", "recusa_origem"]


def _linhas():
    with SEED.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_seed_tem_so_ids_rotulos_e_origem():
    l = _linhas()
    assert list(l[0].keys()) == COLUNAS
    assert len({x["conversa_id"] for x in l}) == len(l)                       # um rótulo por conversa
    assert max(len(x["tema"]) for x in l) < 50                                # tema é rótulo curto, nunca texto de conversa
    assert {x["recusa"] for x in l} <= {"", "true", "false"}


def test_seed_origem_do_llm_sempre_traz_recusa_e_regras_nao():
    for x in _linhas():
        if x["tema_origem"].startswith("openrouter:") or x["recusa_origem"].startswith("openrouter:"):
            assert x["recusa"] in ("true", "false") and x["recusa_origem"] == x["tema_origem"]
        else:
            assert x["recusa"] == "" and x["recusa_origem"] == ""


def _conn():
    psycopg = pytest.importorskip("psycopg")
    if "POSTGRES_DB" not in os.environ:
        pytest.skip("sem banco configurado")
    from loader.migrar import dsn
    try:
        return psycopg.connect(dsn(), connect_timeout=5, autocommit=True)
    except Exception:  # noqa: BLE001
        pytest.skip("banco indisponível")


def test_numero_oficial_nao_muda_com_o_seed_do_llm():
    with _conn() as c:
        if c.execute("SELECT count(*) FROM stg.conversa").fetchone()[0] < 10000:
            pytest.skip("banco sem a base real")
        usuarios, voltaram = c.execute(
            "SELECT usuarios, voltaram_7d FROM mart.agg_retencao_sensibilidade WHERE definicao = 'oficial'").fetchone()
        assert (usuarios, voltaram) == (2372, 566)
        lig = c.execute("SELECT count(*) FILTER (WHERE tema_origem LIKE 'openrouter:%'), count(*) FROM stg.conversa").fetchone()
        assert lig[0] > 0                                                      # o seed novo entrou de fato
        # mesma população elegível independentemente de quem rotulou
        assert c.execute("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE elegivel").fetchone()[0] == 2372


def test_reconciliacao_continua_9_de_9():
    with _conn() as c:
        linhas = c.execute("SELECT * FROM ops.reconciliacao WHERE 1 = (SELECT 1) ORDER BY 1 DESC").fetchall()
        if not linhas:
            pytest.skip("sem reconciliação da base real")
        ultima = [l for l in linhas if l[0] == linhas[0][0]]          # a tabela guarda uma execução por id; vale a mais recente
        assert len(ultima) == 9 and all(l[-1] for l in ultima)
