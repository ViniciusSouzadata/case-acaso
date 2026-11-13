"""Cartão curto de achado (Tela 2): campos opcionais do seed, conferidos contra resultado.* e gravados em resultado.achado (migração 012)."""
import pandas as pd
import psycopg
import pytest

from analise import achados, ajustado, semana
from loader.migrar import dsn


def _grande(pp: float) -> str:
    """Efeito em pontos → texto do número grande: inteiro a partir de 10, uma casa abaixo, com o sinal de menos tipográfico."""
    abs_ = abs(pp)
    texto = f"{abs_:.0f}" if abs_ >= 10 else f"{abs_:.1f}".replace(".", ",")
    return f"{'−' if pp < 0 else '+'}{texto}"


def test_grande_formata_como_a_tela():
    assert _grande(-16.41) == "−16"
    assert _grande(-2.9129) == "−2,9"
    assert _grande(0.52) == "+0,5"


def test_seed_tem_numero_rotulo_e_acao_dos_tres_achados():
    dados = {a["ordem"]: a for a in achados.ler()}
    for ordem in (1, 2, 3):
        for campo in achados.OPCIONAIS:
            assert str(dados[ordem].get(campo, "")).strip(), f"achado {ordem}: {campo} vazio"
    # a ação curta é uma frase só, sem reticências, para caber inteira no cartão
    for a in dados.values():
        assert a["acao_curta"].endswith(".") and "…" not in a["acao_curta"] and len(a["acao_curta"]) <= 90


def test_campos_opcionais_ausentes_viram_nulo(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("- {ordem: 1, titulo: t, evidencia: e, decisao: d, limite: l}\n", encoding="utf-8")
    dados = achados.ler(f)  # opcional: não falha sem os três campos
    assert all(dados[0].get(c) is None for c in achados.OPCIONAIS)


@pytest.mark.usefixtures("usar_real")
def test_numeros_de_destaque_batem_com_resultado():
    with psycopg.connect(dsn(), autocommit=True) as c:
        ajustado.gravar(c)
        efeito = dict(
            c.execute(
                "SELECT fator || '|' || nivel, efeito_ajustado_pp FROM resultado.efeito_fator "
                "WHERE metodo = 'logit_ame' AND efeito_ajustado_pp IS NOT NULL"
            ).fetchall()
        )
        cur = c.execute(semana.SQL)
        df = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
        df["voltou_7d"] = df["voltou_7d"].astype(bool)
        testadas, sig = semana.contar_semanas_significativas(df, semana.n_minimo(c))
    dados = {a["ordem"]: a for a in achados.ler()}
    assert dados[1]["numero_destaque"] == _grande(float(efeito["recusa|sim"]))
    assert dados[2]["numero_destaque"] == _grande(float(efeito["modelo_familia|gpt-4"]))
    assert dados[3]["numero_destaque"] == f"{sig} de {testadas}"


@pytest.mark.usefixtures("usar_real")
def test_gravar_leva_os_campos_para_o_banco():
    with psycopg.connect(dsn(), autocommit=True) as c:
        achados.gravar(c)
        linhas = c.execute("SELECT ordem, numero_destaque, rotulo_destaque, acao_curta FROM resultado.achado ORDER BY ordem").fetchall()
    seed = achados.ler()
    assert linhas == [(a["ordem"], a["numero_destaque"], a["rotulo_destaque"], a["acao_curta"]) for a in seed]
