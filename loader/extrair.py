"""Extração do bruto: snapshot verificável (padrão) ou re-extração completa (FULL_REFRESH=1).

Uso:
    python -m loader.extrair                 # confere o SHA-256 do snapshot
    FULL_REFRESH=1 python -m loader.extrair  # baixa o WildChat-1M, filtra Brasil, regrava snapshot + checksum

Nunca imprime conteúdo de conversa; apenas contagens.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"
RAW_DIR = RAIZ / "data" / "raw" / "wildchat"
REPO_HF = "allenai/WildChat-1M"
PAIS = "Brazil"


class SnapshotInvalido(Exception):
    """Snapshot ausente, sem checksum ou com checksum diferente do registrado."""


def caminho_checksum(caminho: Path) -> Path:
    return caminho.with_suffix(".sha256")


def calcular_sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_checksum(caminho: Path) -> str:
    """Grava `<sha256>  <nome>` (formato do sha256sum) ao lado do arquivo."""
    caminho = Path(caminho)
    digest = calcular_sha256(caminho)
    caminho_checksum(caminho).write_text(f"{digest}  {caminho.name}\n", encoding="utf-8")
    return digest


def verificar_snapshot(caminho: str | Path = SNAPSHOT) -> None:
    """Levanta SnapshotInvalido se o SHA-256 do arquivo não bater com o registrado."""
    caminho = Path(caminho)
    arq_sha = caminho_checksum(caminho)
    if not caminho.is_file():
        raise SnapshotInvalido(f"Snapshot não encontrado: {caminho}. Rode com FULL_REFRESH=1 para recriá-lo.")
    if not arq_sha.is_file():
        raise SnapshotInvalido(f"Checksum não encontrado: {arq_sha}. Não dá para verificar a integridade do snapshot.")
    partes = arq_sha.read_text(encoding="utf-8").split()
    esperado = partes[0].lower() if partes else ""
    obtido = calcular_sha256(caminho)
    if obtido != esperado:
        raise SnapshotInvalido(
            f"SHA-256 do snapshot não confere ({caminho.name}): esperado {esperado or '(vazio)'}, obtido {obtido}. "
            "O arquivo foi alterado ou corrompido; restaure-o do git ou rode com FULL_REFRESH=1."
        )


def _arquivos_raw(raw_dir: Path) -> list[Path]:
    return sorted((raw_dir / "data").glob("*.parquet"))


def garantir_raw(raw_dir: Path = RAW_DIR) -> Path:
    """Reaproveita data/raw/wildchat/data/*.parquet se já existir; senão baixa do Hugging Face (~3,4 GB)."""
    if _arquivos_raw(raw_dir):
        print(f"Reaproveitando {len(_arquivos_raw(raw_dir))} parquets já presentes em {raw_dir}")
        return raw_dir
    from huggingface_hub import snapshot_download

    print(f"Baixando {REPO_HF} (~3,4 GB) para {raw_dir} ...")
    snapshot_download(
        repo_id=REPO_HF, repo_type="dataset", allow_patterns=["data/*.parquet", "README.md"], local_dir=str(raw_dir)
    )
    if not _arquivos_raw(raw_dir):
        raise RuntimeError(f"Download terminou sem parquets em {raw_dir / 'data'}")
    return raw_dir


def extrair_completo(destino: str | Path = SNAPSHOT, raw_dir: Path = RAW_DIR) -> int:
    """FULL_REFRESH: filtra country = 'Brazil' do bruto completo e regrava snapshot + checksum.

    Retorna o número de linhas do novo snapshot. Escreve em arquivo temporário e só então substitui o destino.
    """
    import duckdb

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = garantir_raw(Path(raw_dir))
    origem = (raw_dir / "data" / "*.parquet").as_posix()
    tmp = destino.with_name(destino.name + ".tmp")
    tmp.unlink(missing_ok=True)

    con = duckdb.connect()
    try:
        con.sql("SET memory_limit='2GB'; SET threads=2; SET preserve_insertion_order=false")
        con.sql(
            f"COPY (SELECT * FROM read_parquet('{origem}') WHERE country = '{PAIS}') "
            f"TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        linhas = con.sql(f"SELECT count(*) FROM read_parquet('{tmp.as_posix()}')").fetchall()[0][0]
    finally:
        con.close()
    os.replace(tmp, destino)
    digest = gravar_checksum(destino)
    print(f"Snapshot regravado: {linhas} linhas, sha256={digest}")
    return linhas


def main() -> int:
    try:
        if os.environ.get("FULL_REFRESH") == "1":
            extrair_completo()
        verificar_snapshot(SNAPSHOT)
    except SnapshotInvalido as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    print(f"Snapshot íntegro: {SNAPSHOT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
