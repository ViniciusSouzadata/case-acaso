"""T-105: o parquet sintetico tem o mesmo esquema do bruto real e a contagem esperada."""
from pathlib import Path

import pyarrow.parquet as pq
import pytest

import esperado
import fabrica_bruto

RAIZ = Path(__file__).resolve().parents[1]
REAIS = [RAIZ / "data" / "interim" / "brazil.parquet",
         RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"]


@pytest.fixture(scope="module")
def sintetico(tmp_path_factory):
    return fabrica_bruto.gerar(tmp_path_factory.mktemp("sint") / "sintetico.parquet")


def test_esquema_identico_ao_bruto_real(sintetico):
    real = next((p for p in REAIS if p.exists()), None)
    if real is None:
        pytest.skip("nenhum parquet real encontrado (data/interim/brazil.parquet "
                    "ou data/bruto/wildchat_brasil.parquet)")
    esq_real = pq.read_schema(real)
    esq_sint = pq.read_schema(sintetico)
    assert esq_sint.equals(esq_real, check_metadata=False), f"\nreal:\n{esq_real}\nsint:\n{esq_sint}"


def test_numero_de_linhas(sintetico):
    assert pq.ParquetFile(sintetico).metadata.num_rows == esperado.CONVERSAS_GERADAS
    assert esperado.CONVERSAS_GERADAS == (
        sum(c.n_conversas for c in esperado.CASOS.values()) + esperado.FILLER_CONVERSAS)


def test_formato_dos_turnos(sintetico):
    linhas = pq.read_table(sintetico).to_pylist()
    ids = [t["turn_identifier"] for r in linhas for t in r["conversation"]]
    assert len(ids) == len(set(ids)), "turn_identifier deve ser unico por turno"
    for r in linhas:
        turnos = r["conversation"]
        for t in turnos:
            if t["role"] == "user":
                assert t["timestamp"] is None and t["hashed_ip"] and t["header"]
            else:
                assert t["timestamp"] is not None and t["hashed_ip"] is None and t["header"] is None
        ass = [t for t in turnos if t["role"] == "assistant"]
        if ass:
            assert r["timestamp"] == ass[-1]["timestamp"]
    sem_ass = sum(1 for r in linhas if not any(t["role"] == "assistant" for t in r["conversation"]))
    assert sem_ass == esperado.CONVERSAS_REJEITADAS
    hashes = [r["conversation_hash"] for r in linhas]
    assert len(hashes) - len(set(hashes)) == esperado.CONVERSAS_COM_HASH_REPETIDO - 1
