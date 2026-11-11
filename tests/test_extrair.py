import pytest

from loader.extrair import SnapshotInvalido, gravar_checksum, verificar_snapshot


def _arquivo(tmp_path):
    p = tmp_path / "x.parquet"
    p.write_bytes(b"conteudo de teste" * 1000)
    gravar_checksum(p)
    return p


def test_arquivo_integro_passa(tmp_path):
    verificar_snapshot(_arquivo(tmp_path))


def test_arquivo_alterado_falha_com_mensagem_clara(tmp_path):
    p = _arquivo(tmp_path)
    p.write_bytes(p.read_bytes() + b"x")
    with pytest.raises(SnapshotInvalido, match="SHA-256 do snapshot não confere"):
        verificar_snapshot(p)


def test_sem_checksum_falha(tmp_path):
    p = _arquivo(tmp_path)
    p.with_suffix(".sha256").unlink()
    with pytest.raises(SnapshotInvalido, match="Checksum não encontrado"):
        verificar_snapshot(p)


def test_snapshot_ausente_falha(tmp_path):
    with pytest.raises(SnapshotInvalido, match="Snapshot não encontrado"):
        verificar_snapshot(tmp_path / "nada.parquet")


def test_snapshot_real_confere_e_tem_11621_linhas():
    import duckdb

    from loader.extrair import SNAPSHOT

    verificar_snapshot(SNAPSHOT)
    n = duckdb.connect().sql(f"SELECT count(*) FROM read_parquet('{SNAPSHOT.as_posix()}')").fetchall()[0][0]
    assert n == 11621
