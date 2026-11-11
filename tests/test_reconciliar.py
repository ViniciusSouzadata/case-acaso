"""T-108: reconciliação bruto x marts. Passa no sintético e no snapshot real; divergência injetada falha com
código != 0 e marca o lote. Nunca imprime texto de conversa."""
import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

import esperado
from conftest import restaurar_sint
from loader import carregar, migrar, reconciliar

SNAPSHOT = Path(carregar.SNAPSHOT)
METRICAS = ["conversas_lidas", "conversas_aceitas", "ips_distintos", "usuarios_oficiais", "elegiveis", "voltaram_7d",
            "semanas_maduras", "semanas_com_novos_divergentes", "semanas_com_voltaram_divergentes"]


def _q(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args or None).fetchall()


def _gravadas():
    return {r[0]: r[1:] for r in _q(
        "SELECT metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok FROM ops.reconciliacao "
        "WHERE lote_id = (SELECT max(lote_id) FROM ops.lote_carga WHERE status = 'sucesso')")}


def _mexer(sql):
    with psycopg.connect(migrar.dsn(), autocommit=True) as c:
        c.execute(sql)


def _rodar_cli(parquet):
    return subprocess.run([sys.executable, "-m", "loader.reconciliar"], capture_output=True, text=True,
                          env={**os.environ, "BRUTO_CAMINHO": str(parquet)}, cwd=carregar.RAIZ)


@pytest.mark.usefixtures("usar_sint")
class TestSintetico:
    def test_passa_e_grava_uma_linha_por_metrica(self, sint_parquet):
        linhas = reconciliar.reconciliar(sint_parquet)
        assert [l[0] for l in linhas] == METRICAS
        g = _gravadas()
        assert list(g) == METRICAS and all(v[4] for v in g.values())
        assert g["conversas_lidas"][:2] == (esperado.CONVERSAS_GERADAS, esperado.CONVERSAS_GERADAS)
        assert g["conversas_aceitas"][0] == esperado.CONVERSAS_CARREGADAS
        assert g["ips_distintos"][0] == esperado.IPS_DISTINTOS - 1  # a conversa rejeitada (I) não entra
        assert g["usuarios_oficiais"][0] == esperado.USUARIOS_OFICIAIS
        assert g["elegiveis"][0] == esperado.USUARIOS_ELEGIVEIS
        assert g["voltaram_7d"][0] == esperado.RETORNOS_ENTRE_ELEGIVEIS
        assert g["semanas_maduras"][0] > 0
        assert g["semanas_com_novos_divergentes"][:3] == (0, 0, 0) and g["semanas_com_voltaram_divergentes"][:3] == (0, 0, 0)
        assert _rodar_cli(sint_parquet).returncode == 0

    def test_rodar_de_novo_nao_duplica_linhas(self, sint_parquet):
        reconciliar.reconciliar(sint_parquet)
        reconciliar.reconciliar(sint_parquet)
        assert len(_gravadas()) == len(METRICAS)
        assert _q("SELECT count(*) FROM ops.reconciliacao WHERE lote_id = (SELECT max(lote_id) FROM ops.lote_carga "
                  "WHERE status = 'sucesso')")[0][0] == len(METRICAS)

    @pytest.mark.parametrize("sabotagem,metricas_que_divergem", [
        ("DELETE FROM mart.dim_usuario WHERE usuario_id = (SELECT usuario_id FROM mart.dim_usuario WHERE elegivel LIMIT 1)",
         {"usuarios_oficiais", "elegiveis"}),
        ("UPDATE mart.fct_primeira_experiencia SET voltou_7d = NOT voltou_7d "
         "WHERE usuario_id = (SELECT usuario_id FROM mart.fct_primeira_experiencia WHERE elegivel LIMIT 1)",
         {"voltaram_7d"}),
        ("UPDATE mart.agg_retencao_periodo SET novos = novos + 1 WHERE granularidade = 'semana' AND madura "
         "AND periodo = (SELECT min(periodo) FROM mart.agg_retencao_periodo WHERE granularidade = 'semana' AND madura)",
         {"semanas_com_novos_divergentes"}),
    ], ids=["linha_apagada_da_dim_usuario", "voltou_7d_alterado", "novos_da_semana_alterado"])
    def test_divergencia_injetada_falha_e_marca_o_lote(self, sint_parquet, sabotagem, metricas_que_divergem):
        try:
            _mexer(sabotagem)
            r = _rodar_cli(sint_parquet)
            assert r.returncode != 0
            for m in metricas_que_divergem:
                assert m in r.stderr and "diferença" in r.stderr, r.stderr
            status, erro = _q("SELECT status, erro FROM ops.lote_carga ORDER BY lote_id DESC LIMIT 1")[0]
            assert status == "falha" and all(m in erro for m in metricas_que_divergem), (status, erro)
            ruins = {m for m, (_, _, _, _, ok) in _gravadas_do_lote_falho().items() if not ok}
            assert metricas_que_divergem <= ruins
        finally:
            restaurar_sint(sint_parquet)  # nova carga (lote 'sucesso') + retransformação
        reconciliar.reconciliar(sint_parquet)  # voltou ao normal


def _gravadas_do_lote_falho():
    return {r[0]: r[1:] for r in _q(
        "SELECT metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok FROM ops.reconciliacao "
        "WHERE lote_id = (SELECT max(lote_id) FROM ops.lote_carga WHERE status = 'falha')")}


@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="snapshot real ausente")
@pytest.mark.usefixtures("usar_real")
def test_passa_no_snapshot_real():
    linhas = reconciliar.reconciliar()  # BRUTO_CAMINHO padrão = snapshot
    g = {l[0]: l[1:] for l in linhas}
    assert all(v[4] for v in g.values()), g
    assert g["conversas_lidas"][:2] == (11621, 11621)
    assert (g["usuarios_oficiais"][0], g["elegiveis"][0], g["voltaram_7d"][0]) == (2498, 2372, 566)
    assert g["semanas_maduras"][0] == 53
    assert len(_gravadas()) == len(METRICAS)
