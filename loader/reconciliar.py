"""Reconciliação bruto x marts (T-108).

Recalcula DIRETO DO PARQUET (o mesmo BRUTO_CAMINHO da carga) com SQL DuckDB escrito à parte do SQL dos marts
(sql/transform, mart.calc_retencao) e compara com `stg`/`mart`. Uma linha por métrica em `ops.reconciliacao`,
referente ao último lote com status 'sucesso'. Tolerância 0 para contagens. Qualquer divergência: mensagem com
a métrica e a diferença, lote mais recente marcado 'falha' (motivo em `erro`) e código de saída 1.

LIMITE DA INDEPENDÊNCIA: as regras de sessão, retorno, elegibilidade e coorte são reescritas aqui em DuckDB, sem
importar nada de derivar.py. Só a normalização da chave de usuário (minúsculas, sem bordas) e a família de
user-agent (derivar.familia_so / familia_navegador) são reaproveitadas: um erro nelas passa despercebido por esta
reconciliação (são cobertas pelos testes unitários de derivar.py). Limiares vêm de ops.parametros.

Métricas gravadas (valor_bruto = recalculado do parquet; valor_mart = lido de stg/mart):
  conversas_lidas, conversas_aceitas, ips_distintos, usuarios_oficiais, elegiveis, voltaram_7d,
  semanas_maduras, semanas_com_novos_divergentes, semanas_com_voltaram_divergentes.
Nas duas últimas, valor_bruto = nº de semanas divergentes e valor_mart = 0 (esperado). Nunca imprime texto de conversa.

Uso:  python -m loader.reconciliar        (BRUTO_CAMINHO opcional)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import duckdb
import psycopg

from loader import derivar
from loader.extrair import SNAPSHOT
from loader.migrar import dsn

TOLERANCIA = 0


class ReconciliacaoDivergente(Exception):
    """Pelo menos uma métrica fora da tolerância."""


# ----------------------------------------------------------------------------------------------- lado bruto
# Conversas aceitas = as que a carga deveria gravar: id não nulo, >= 1 resposta com timestamp, início <= fim,
# sem id repetido. "Uso" = >= 1 mensagem de usuário não vazia (aceitas já têm >= 1 resposta).
_SQL_CONVERSAS = """
CREATE TEMP TABLE bruto AS
SELECT conversation[1].turn_identifier                                                   AS id,
       hashed_ip                                                                         AS ip,
       struct_extract(header, 'user-agent')                                              AS ua,
       timezone('UTC', list_filter(conversation, lambda t: t.role = 'assistant')[1].timestamp) AS ini,
       timezone('UTC', timestamp)                                                        AS fim,
       len(list_filter(conversation, lambda t: t.role = 'user'
                       AND trim(coalesce(t.content, '')) <> '')) > 0                     AS msg_usuario
FROM read_parquet(?)
"""

_SQL_ACEITAS = """
CREATE TEMP TABLE aceitas AS
SELECT * FROM bruto
WHERE id IS NOT NULL AND ini IS NOT NULL AND (fim IS NULL OR ini <= fim)
QUALIFY row_number() OVER (PARTITION BY id ORDER BY ini) = 1
"""

# Usuário oficial = (ip, SO, navegador) normalizados; só conversas com uso e IP não vazio.
_SQL_USO = """
CREATE TEMP TABLE uso AS
SELECT a.id, a.ini, a.fim, a.ip,
       lower(trim(a.ip)) || '|' || f.so || '|' || f.nav AS u
FROM aceitas a JOIN ua_familia f ON f.ua IS NOT DISTINCT FROM a.ua
WHERE a.msg_usuario AND trim(coalesce(a.ip, '')) <> ''
"""

# Sessão nova quando o intervalo entre o FIM da conversa anterior e o INÍCIO da atual passa de `gap`.
_SQL_USUARIOS = """
CREATE TEMP TABLE usuarios AS
WITH marc AS (
    SELECT u, id, ini, ip,
           CASE WHEN lag(fim) OVER w IS NULL OR ini - lag(fim) OVER w > to_minutes(?::int) THEN 1 ELSE 0 END AS nova
    FROM uso WINDOW w AS (PARTITION BY u ORDER BY ini, id)
),
seqs AS (
    SELECT u, ip, ini, sum(nova) OVER (PARTITION BY u ORDER BY ini, id) AS seq FROM marc
),
sessoes AS (SELECT u, seq, min(ini) AS ini, min(ip) AS ip FROM seqs GROUP BY u, seq),
primeira AS (SELECT u, ini AS ini1, ip FROM sessoes WHERE seq = 1),
base AS (SELECT min(ini) AS inicio, max(fim) AS fim FROM aceitas),
ips AS (
    SELECT ip, (count(*) >= ?::int OR count(DISTINCT ua) >= ?::int) AS anomalo FROM aceitas GROUP BY ip
)
SELECT p.u,
       p.ini1,
       EXISTS (SELECT 1 FROM sessoes s WHERE s.u = p.u AND s.seq > 1 AND s.ini <= p.ini1 + to_hours(?::int)) AS voltou,
       (p.ini1 + to_hours(?::int) <= b.fim)                     AS maduro,
       (p.ini1 < b.inicio + to_days(?::int))                    AS burn_in,
       coalesce(i.anomalo, false)                               AS anomalo
FROM primeira p CROSS JOIN base b LEFT JOIN ips i ON i.ip = p.ip
"""


def _ler_parametros(conn: psycopg.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT chave, valor FROM ops.parametros").fetchall())


def calcular_bruto(caminho: Path, par: dict[str, str]) -> dict[str, Any]:
    """Recalcula tudo do parquet. Devolve contagens e {semana: (novos, voltaram)} das semanas maduras."""
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET threads=2")
        con.execute("SET TimeZone='UTC'")
        con.execute(_SQL_CONVERSAS, [Path(caminho).as_posix()])
        con.execute(_SQL_ACEITAS)
        # família de user-agent: único ponto reaproveitado de derivar.py (ver docstring do módulo)
        uas = [r[0] for r in con.execute("SELECT DISTINCT ua FROM aceitas").fetchall()]
        con.execute("CREATE TEMP TABLE ua_familia (ua VARCHAR, so VARCHAR, nav VARCHAR)")
        con.executemany("INSERT INTO ua_familia VALUES (?, ?, ?)",
                        [(ua, derivar.familia_so(ua), derivar.familia_navegador(ua)) for ua in uas])
        con.execute(_SQL_USO)
        con.execute(_SQL_USUARIOS, [
            int(par["gap_sessao_min"]), int(par["limiar_conversas_ip"]), int(par["limiar_uas_ip"]),
            int(par["janela_retorno_horas"]), int(par["janela_retorno_horas"]), int(par["burn_in_dias"]),
        ])
        lidas = con.execute("SELECT count(*) FROM bruto").fetchall()[0][0]
        aceitas = con.execute("SELECT count(*) FROM aceitas").fetchall()[0][0]
        ips = con.execute("SELECT count(DISTINCT ip) FROM aceitas").fetchall()[0][0]
        n_usuarios = con.execute("SELECT count(*) FROM usuarios").fetchall()[0][0]
        eleg = con.execute(
            "SELECT count(*), count(*) FILTER (WHERE voltou) FROM usuarios WHERE maduro AND NOT burn_in AND NOT anomalo"
        ).fetchall()[0]
        # coorte semanal (segunda-feira, horário local); semana madura = todos os seus usuários são maduros
        semanas = con.execute(
            """
            WITH c AS (
                SELECT date_trunc('week', timezone(?, timezone('UTC', ini1)))::date AS semana, maduro, voltou
                FROM usuarios WHERE NOT burn_in AND NOT anomalo
            )
            SELECT semana, count(*), count(*) FILTER (WHERE voltou)
            FROM c GROUP BY semana HAVING bool_and(maduro) ORDER BY semana
            """, [par["fuso_pais"]]).fetchall()
        return {"lidas": lidas, "aceitas": aceitas, "ips": ips, "usuarios": n_usuarios,
                "elegiveis": eleg[0], "voltaram": eleg[1],
                "semanas": {s: (int(n), int(v)) for s, n, v in semanas}}
    finally:
        con.close()


# ------------------------------------------------------------------------------------------------ lado marts
def ler_marts(conn: psycopg.Connection, lote_id: int) -> dict[str, Any]:
    um = lambda sql, *a: conn.execute(sql, a or None).fetchone()  # noqa: E731
    rejeitadas = um("SELECT count(*) FROM ops.rejeitado WHERE lote_id = %s", lote_id)[0]
    n_stg = um("SELECT count(*) FROM stg.conversa")[0]
    eleg = um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel")[0]
    vol = um("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE elegivel AND voltou_7d")[0]
    semanas = conn.execute(
        "SELECT periodo, novos, coalesce(voltaram_7d, 0) FROM mart.agg_retencao_periodo "
        "WHERE granularidade = 'semana' AND madura").fetchall()
    return {"lidas": n_stg + rejeitadas, "aceitas": n_stg,
            "ips": um("SELECT count(DISTINCT hashed_ip) FROM stg.conversa")[0],
            "usuarios": um("SELECT count(*) FROM mart.dim_usuario")[0],
            "elegiveis": eleg, "voltaram": vol,
            "semanas": {s: (int(n), int(v)) for s, n, v in semanas}}


def comparar(bruto: dict[str, Any], mart: dict[str, Any]) -> list[tuple[str, int, int, int, int, bool]]:
    """Linhas (metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok). Tolerância 0 em tudo."""
    linhas = []

    def add(metrica, vb, vm):
        dif = vb - vm
        linhas.append((metrica, vb, vm, dif, TOLERANCIA, abs(dif) <= TOLERANCIA))

    add("conversas_lidas", bruto["lidas"], mart["lidas"])
    add("conversas_aceitas", bruto["aceitas"], mart["aceitas"])
    add("ips_distintos", bruto["ips"], mart["ips"])
    add("usuarios_oficiais", bruto["usuarios"], mart["usuarios"])
    add("elegiveis", bruto["elegiveis"], mart["elegiveis"])
    add("voltaram_7d", bruto["voltaram"], mart["voltaram"])
    sb, sm = bruto["semanas"], mart["semanas"]
    add("semanas_maduras", len(sb), len(sm))
    todas = set(sb) | set(sm)  # semana que existe só de um lado conta como divergente
    add("semanas_com_novos_divergentes", sum(sb.get(s, (None, None))[0] != sm.get(s, (None, None))[0] for s in todas), 0)
    add("semanas_com_voltaram_divergentes", sum(sb.get(s, (None, None))[1] != sm.get(s, (None, None))[1] for s in todas), 0)
    return linhas


def _mensagem(linhas) -> str:
    return "; ".join(f"{m}: bruto={vb} mart={vm} diferença={d} (tolerância {t})"
                     for m, vb, vm, d, t, ok in linhas if not ok)


def reconciliar(caminho_bruto: str | Path | None = None) -> list[tuple]:
    """Recalcula, grava ops.reconciliacao e levanta ReconciliacaoDivergente (marcando o lote 'falha') se algo diverge."""
    caminho = Path(caminho_bruto or os.environ.get("BRUTO_CAMINHO") or SNAPSHOT)
    with psycopg.connect(dsn(), autocommit=True) as conn:
        ref = conn.execute(
            "SELECT lote_id FROM ops.lote_carga WHERE status = 'sucesso' ORDER BY lote_id DESC LIMIT 1").fetchone()
        if ref is None:
            raise RuntimeError("nenhum lote com status 'sucesso' em ops.lote_carga: rode a carga antes de reconciliar")
        lote_id = ref[0]
        bruto = calcular_bruto(caminho, _ler_parametros(conn))
        linhas = comparar(bruto, ler_marts(conn, lote_id))
        with conn.transaction():
            conn.execute("DELETE FROM ops.reconciliacao WHERE lote_id = %s", (lote_id,))
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO ops.reconciliacao (lote_id, metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)", [(lote_id, *l) for l in linhas])
        if not all(l[-1] for l in linhas):
            msg = _mensagem(linhas)
            conn.execute(  # o lote mais recente (não necessariamente o de referência) fica 'falha'
                "UPDATE ops.lote_carga SET status = 'falha', terminado_em = coalesce(terminado_em, now()), erro = %s "
                "WHERE lote_id = (SELECT max(lote_id) FROM ops.lote_carga)", (f"reconciliacao: {msg}"[:2000],))
            raise ReconciliacaoDivergente(msg)
    return linhas


def main() -> int:
    try:
        linhas = reconciliar()
    except ReconciliacaoDivergente as e:
        print(f"RECONCILIAÇÃO FALHOU, lote marcado como falha. Divergências -> {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERRO na reconciliação: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    for m, vb, vm, d, t, ok in linhas:
        print(f"  {'ok ' if ok else 'ERRO'} {m}: bruto={vb} mart={vm} diferença={d}")
    print(f"Reconciliação ok: {len(linhas)} métricas, tolerância {TOLERANCIA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
