"""T-501: a consulta de confirmação do incidente roda no bruto e mostra o mecanismo (caso E: 1 IP, 12 user-agents)."""
import sys
from datetime import date
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import incidente_confirmacao as inc  # noqa: E402

from loader.migrar import dsn  # noqa: E402

SQL = Path(__file__).resolve().parent.parent / "docs" / "incidente" / "confirmacao.sql"


def test_caso_e_um_ip_doze_uas_infla_novos_pela_chave_do_incidente(sint_parquet):
    r = inc.calcular(sint_parquet)
    assert r["max_uas_por_ip"] == 12                                    # o IP do caso E
    semana_e = next(s for s in r["semanas"] if s["semana"] == date(2024, 2, 19))   # 20/02/2024 cai na semana de 19/02
    assert semana_e["max_uas_novos_por_ip"] == 12
    assert semana_e["novos_ip_ua"] - semana_e["novos_ip"] >= 11         # 12 "novos" pela chave IP+UA contra 1 pela chave IP
    assert r["usuarios_ip_ua"] > r["usuarios_ip"]
    assert sum(s["novos_ip"] for s in r["semanas"]) == r["usuarios_ip"]
    assert sum(s["novos_ip_ua"] for s in r["semanas"]) == r["usuarios_ip_ua"]
    assert sum(s["novos_em_ip_ja_visto"] for s in r["semanas"]) == r["usuarios_ip_ua"] - r["usuarios_ip"]   # todo "novo" a mais cai em IP já visto


def test_relatorio_traz_so_agregados(sint_parquet):
    texto = inc.relatorio(inc.calcular(sint_parquet))
    assert "Máximo de user-agents diferentes em um único IP: **12**" in texto
    assert "Mozilla" not in texto and len(max(texto.splitlines(), key=len)) < 400


@pytest.mark.usefixtures("usar_sint")
def test_versao_postgres_da_consulta_bate_com_a_do_duckdb(sint_parquet):
    esperado = {s["semana"]: (s["novos_ip"], s["novos_ip_ua"], s["novos_em_ip_ja_visto"], s["max_uas_novos_por_ip"])
                for s in inc.calcular(sint_parquet)["semanas"]}
    with psycopg.connect(dsn(), autocommit=True) as c:
        # no sintético só contam as conversas que entraram na carga (a rejeitada do caso I não chega a stg)
        pg = {l[0]: tuple(int(x) for x in l[1:]) for l in c.execute(SQL.read_text(encoding="utf-8")).fetchall()}
    assert pg.keys() <= esperado.keys()
    assert pg[date(2024, 2, 19)] == esperado[date(2024, 2, 19)]
