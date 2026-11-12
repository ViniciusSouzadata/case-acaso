"""Carga (T-104): bruto (parquet) -> derivação -> stg.conversa. Texto de conversa nunca é gravado nem logado.

Uso:  python -m loader.carregar
Variáveis de ambiente (todas opcionais):
  BRUTO_CAMINHO          parquet de entrada (padrão: data/bruto/wildchat_brasil.parquet)
  REGRAS_RECUSA_CAMINHO  YAML de recusa (padrão: seeds/regras_recusa.yaml)
  TEMA_SEED_CAMINHO      CSV conversa_id,tema,tema_origem (padrão: seeds/tema_conversa.csv; opcional)

Integridade: se existir `<arquivo>.sha256` ao lado do parquet, `verificar_snapshot` roda antes da leitura
(snapshot real). Sem esse arquivo (caso do parquet sintético dos testes) a verificação é pulada.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import timezone
from pathlib import Path
from typing import Any

import duckdb
import psycopg
import yaml

from loader import derivar
from loader.extrair import RAIZ, SNAPSHOT, calcular_sha256, caminho_checksum, verificar_snapshot
from loader.migrar import dsn

REGRAS_RECUSA = RAIZ / "seeds" / "regras_recusa.yaml"
TEMA_SEED = RAIZ / "seeds" / "tema_conversa.csv"

# Uma linha por conversa. Textos saem só para a derivação em memória (tamanho/flag); timestamps em UTC ingênuo.
CONSULTA = """
SELECT
  conversation[1].turn_identifier                                         AS conversa_id,
  conversation_hash,
  count(*) OVER (PARTITION BY conversation_hash) > 1                      AS hash_repetido,
  hashed_ip,
  struct_extract(header, 'user-agent')                                    AS user_agent,
  struct_extract(header, 'accept-language')                               AS accept_language,
  model,
  timezone('UTC', list_filter(conversation, lambda t: t.role = 'assistant')[1].timestamp) AS ts_inicio,
  timezone('UTC', timestamp)                                              AS ts_fim,
  turn,
  language                                                                AS idioma_conversa,
  list_transform(list_filter(conversation, lambda t: t.role = 'user'), lambda t: t.content) AS mensagens_usuario,
  list_filter(conversation, lambda t: t.role = 'user')[1].language        AS idioma_usuario_1,
  list_filter(conversation, lambda t: t.role = 'assistant')[1].content    AS resposta_1,
  list_filter(conversation, lambda t: t.role = 'assistant')[1].language   AS idioma_resposta_1,
  len(list_filter(conversation, lambda t: t.role = 'assistant'))          AS n_respostas_assistente,
  state                                                                   AS estado,
  redacted,
  len(list_filter(conversation, lambda t: t.role = 'user' AND t.hashed_ip IS NOT NULL
                  AND hashed_ip IS NOT NULL AND t.hashed_ip <> hashed_ip)) > 0 AS ip_mudou
FROM read_parquet(?)
"""

COLUNAS = [
    "conversa_id", "conversation_hash", "hash_repetido", "hashed_ip", "user_agent", "accept_language",
    "ua_so", "ua_navegador", "ua_dispositivo", "usuario_id", "usuario_id_ip", "usuario_id_ip_ua",
    "modelo_versao", "modelo_familia", "ts_inicio", "ts_fim", "n_turnos",
    "idioma_conversa", "idioma_pergunta_1", "idioma_resposta_1", "idioma_divergente",
    "estado", "fuso", "chars_pergunta_1", "chars_resposta_1", "recusa_1", "pergunta_vazia",
    "conta_como_uso", "ip_mudou", "redacted", "tema", "tema_origem", "recusa_origem", "lote_id",
]


def carregar_regras_recusa(caminho: Path) -> tuple[str, list[str]]:
    """(versao, padrões em minúsculas) do YAML versionado."""
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    padroes = [p.lower() for grupo in dados["padroes"].values() for p in grupo]
    return str(dados["versao"]), padroes


def carregar_tema_seed(caminho: Path) -> dict[int, tuple[str, str | None]]:
    """conversa_id -> (tema, tema_origem). Arquivo ausente = seed vazio (tema 'não classificado')."""
    caminho = Path(caminho)
    if not caminho.is_file():
        return {}
    with open(caminho, encoding="utf-8", newline="") as f:
        return {int(l["conversa_id"]): (l["tema"], l.get("tema_origem") or None) for l in csv.DictReader(f)}


def ler_bruto(caminho: Path) -> tuple[list[str], list[tuple]]:
    """Lê o parquet com DuckDB (2 GB, 2 threads) e devolve (nomes das colunas, linhas)."""
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET threads=2")
        con.execute("SET TimeZone='UTC'")
        cur = con.execute(CONSULTA, [Path(caminho).as_posix()])
        nomes = [d[0] for d in cur.description]
        return nomes, cur.fetchall()
    finally:
        con.close()


def _utc(dt):
    return dt.replace(tzinfo=timezone.utc) if dt is not None else None


def carregar_recusa_seed(caminho: Path) -> dict[int, tuple[bool, str]]:
    """conversa_id -> (recusa, origem) das linhas do seed com a coluna `recusa` preenchida (classificador LLM).
    Sem arquivo ou sem a coluna = vazio: a recusa continua vindo das regras de palavras-chave."""
    caminho = Path(caminho)
    if not caminho.is_file():
        return {}
    with open(caminho, encoding="utf-8", newline="") as f:
        return {int(l["conversa_id"]): (l["recusa"].strip().lower() == "true", l.get("recusa_origem") or "llm")
                for l in csv.DictReader(f) if (l.get("recusa") or "").strip().lower() in ("true", "false")}


def processar(nomes: list[str], linhas: list[tuple], padroes: list[str],
              tema_seed: dict, recusa_seed: dict | None = None) -> tuple[list[dict], list[tuple[Any, str]]]:
    """Deriva e separa aceitas de rejeitadas [(conversa_id, motivo)]. Puro em relação ao banco."""
    aceitas: list[dict] = []
    rejeitadas: list[tuple[Any, str]] = []
    vistos: set[int] = set()
    for linha in linhas:
        bruto = dict(zip(nomes, linha))
        bruto["ts_inicio"] = _utc(bruto["ts_inicio"])
        bruto["ts_fim"] = _utc(bruto["ts_fim"])
        motivo = derivar.motivo_rejeicao(
            bruto["conversa_id"], bruto["n_respostas_assistente"], bruto["ts_inicio"], bruto["ts_fim"]
        )
        if motivo is None and bruto["conversa_id"] in vistos:
            motivo = derivar.MOTIVO_ID_DUPLICADO
        if motivo:
            rejeitadas.append((bruto["conversa_id"], motivo))
            continue
        vistos.add(bruto["conversa_id"])
        if recusa_seed and bruto["conversa_id"] in recusa_seed:
            bruto["recusa_seed"] = recusa_seed[bruto["conversa_id"]]
        aceitas.append(derivar.derivar_conversa(bruto, padroes, tema_seed))
    return aceitas, rejeitadas


def _gravar_staging(conn: psycopg.Connection, registros: list[dict], lote_id: int) -> None:
    """COPY para tabela temporária e upsert por conversa_id (uma instrução, ~12 mil linhas)."""
    conn.execute("CREATE TEMP TABLE _stg_conversa_tmp (LIKE stg.conversa) ON COMMIT DROP")
    lista = ", ".join(COLUNAS)
    with conn.cursor() as cur:
        with cur.copy(f"COPY _stg_conversa_tmp ({lista}) FROM STDIN") as copia:
            for r in registros:
                copia.write_row([lote_id if c == "lote_id" else r[c] for c in COLUNAS])
    atualizar = ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUNAS if c != "conversa_id")
    conn.execute(
        f"INSERT INTO stg.conversa ({lista}) SELECT {lista} FROM _stg_conversa_tmp "
        f"ON CONFLICT (conversa_id) DO UPDATE SET {atualizar}"
    )


def carregar(caminho_bruto: str | Path | None = None) -> dict[str, Any]:
    """Executa uma carga completa em UMA transação e devolve o resumo do lote."""
    caminho = Path(caminho_bruto or os.environ.get("BRUTO_CAMINHO") or SNAPSHOT)
    if caminho_checksum(caminho).is_file():
        verificar_snapshot(caminho)  # snapshot real: confere integridade antes de ler
    versao_recusa, padroes = carregar_regras_recusa(Path(os.environ.get("REGRAS_RECUSA_CAMINHO") or REGRAS_RECUSA))
    tema_seed = carregar_tema_seed(Path(os.environ.get("TEMA_SEED_CAMINHO") or TEMA_SEED))
    recusa_seed = carregar_recusa_seed(Path(os.environ.get("TEMA_SEED_CAMINHO") or TEMA_SEED))
    sha = calcular_sha256(caminho)

    # Lote registrado em conexão própria (autocommit): sobrevive ao rollback dos dados.
    with psycopg.connect(dsn(), autocommit=True) as ctl:
        versao_def = ctl.execute("SELECT valor FROM ops.parametros WHERE chave = 'versao_definicao'").fetchone()[0]
        lote_id = ctl.execute(
            "INSERT INTO ops.lote_carga (fonte, sha256, versao_definicao, status) "
            "VALUES (%s, %s, %s, 'em_andamento') RETURNING lote_id",
            (caminho.name, sha, versao_def),
        ).fetchone()[0]
        try:
            nomes, linhas = ler_bruto(caminho)
            aceitas, rejeitadas = processar(nomes, linhas, padroes, tema_seed, recusa_seed)
            with psycopg.connect(dsn()) as conn:  # transação única; rollback automático em exceção
                if rejeitadas:
                    with conn.cursor() as cur:
                        cur.executemany(
                            "INSERT INTO ops.rejeitado (lote_id, conversa_id, motivo) VALUES (%s, %s, %s)",
                            [(lote_id, cid, mot) for cid, mot in rejeitadas],
                        )
                _gravar_staging(conn, aceitas, lote_id)
                conn.execute(
                    "UPDATE ops.lote_carga SET terminado_em = now(), linhas_lidas = %s, linhas_gravadas = %s, "
                    "linhas_rejeitadas = %s, status = 'sucesso' WHERE lote_id = %s",
                    (len(linhas), len(aceitas), len(rejeitadas), lote_id),
                )
        except Exception as e:
            ctl.execute(
                "UPDATE ops.lote_carga SET terminado_em = now(), status = 'falha', erro = %s WHERE lote_id = %s",
                (f"{type(e).__name__}: {e}"[:2000], lote_id),
            )
            raise
    return {"lote_id": lote_id, "lidas": len(linhas), "gravadas": len(aceitas), "rejeitadas": len(rejeitadas),
            "versao_recusa": versao_recusa}


def main() -> int:
    t0 = time.time()
    try:
        r = carregar()
    except Exception as e:
        print(f"ERRO na carga: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"Lote {r['lote_id']}: lidas={r['lidas']} gravadas={r['gravadas']} rejeitadas={r['rejeitadas']} "
          f"(regras_recusa v{r['versao_recusa']}) em {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
