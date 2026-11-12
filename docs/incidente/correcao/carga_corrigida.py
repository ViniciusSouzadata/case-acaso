"""Correção escrita da carga (incidente §4.2). Código de documentação: sintaticamente válido, não roda sozinho.

Defeitos que resolve (cada um marcado com `# DEFEITO:` na linha onde aparece a correção):
  1. identidade de usuário montada à mão na carga (`ip|user-agent`) -> uma regra única, versionada, usada por todo mundo;
  2. `ON CONFLICT DO NOTHING` congelava conversa que continua em outro dia -> upsert idempotente;
  3. inserção linha a linha, sem transação -> um lote em uma transação, tudo ou nada;
  4. sem registro do que foi lido, gravado e rejeitado -> linha em `ops.lote_carga` por execução.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable, Sequence

VERSAO_DEFINICAO = "1.0.0"


# ----------------------------------------------------------------------------- 1. identidade: uma regra só
def familia_so(ua: str | None) -> str:
    ua = (ua or "").lower()
    for nome, marca in (("android", "android"), ("ios", "iphone"), ("windows", "windows"), ("mac", "mac os"), ("linux", "linux")):
        if marca in ua:
            return nome
    return "outro"


def familia_navegador(ua: str | None) -> str:
    ua = (ua or "").lower()
    for nome, marca in (("edge", "edg/"), ("opera", "opr/"), ("firefox", "firefox"), ("chrome", "chrome"), ("safari", "safari")):
        if marca in ua:
            return nome
    return "outro"


def usuario_id(hashed_ip: str | None, user_agent: str | None) -> str | None:
    """DEFEITO: `f"{hashed_ip}|{user_agent}"` tratava cada versão de navegador como pessoa nova (+21% de "usuários" no Brasil).
    A regra oficial usa IP + família de sistema + família de navegador (sem a versão), e vive só aqui."""
    if not hashed_ip:
        return None
    chave = "|".join([hashed_ip, familia_so(user_agent), familia_navegador(user_agent)])
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------- 2. upsert idempotente
COLUNAS = ("conversa_id", "usuario_id", "ts_inicio", "ts_fim", "n_turnos", "lote_id")

SQL_UPSERT = (
    "INSERT INTO stg.conversa ({colunas}) VALUES ({marcas}) "
    "ON CONFLICT (conversa_id) DO UPDATE SET {atualiza}"  # DEFEITO: DO NOTHING deixava turnos e fim velhos para sempre
).format(
    colunas=", ".join(COLUNAS),
    marcas=", ".join(["%s"] * len(COLUNAS)),
    atualiza=", ".join(f"{c} = EXCLUDED.{c}" for c in COLUNAS if c != "conversa_id"),
)


# ----------------------------------------------------------------------------- 3 e 4. um lote, uma transação, um registro
def carregar_lote(conn, conversas: Iterable[dict], fonte: str, sha256: str) -> dict:
    """`conn` é uma conexão psycopg. Tudo ou nada: se qualquer linha falhar, nada do lote fica e o lote registra 'falha'."""
    lote_id = conn.execute(
        "INSERT INTO ops.lote_carga (fonte, sha256, versao_definicao, status) VALUES (%s, %s, %s, 'em_andamento') RETURNING lote_id",
        (fonte, sha256, VERSAO_DEFINICAO),
    ).fetchone()[0]
    conn.commit()  # o registro do lote existe mesmo se a carga falhar
    lidas = gravadas = 0
    rejeitadas: list[tuple[int | None, str]] = []
    try:
        with conn.transaction():  # DEFEITO: antes cada linha era um INSERT solto; carga parcial passava em silêncio
            for c in conversas:
                lidas += 1
                motivo = _motivo_rejeicao(c)
                if motivo:
                    rejeitadas.append((c.get("conversa_id"), motivo))
                    continue
                uid = usuario_id(c.get("hashed_ip"), c.get("user_agent"))
                conn.execute(SQL_UPSERT, (c["conversa_id"], uid, c["ts_inicio"], c["ts_fim"], c["n_turnos"], lote_id))
                gravadas += 1
            for cid, motivo in rejeitadas:
                conn.execute("INSERT INTO ops.rejeitado (lote_id, conversa_id, motivo) VALUES (%s, %s, %s)", (lote_id, cid, motivo))
        conn.execute(
            "UPDATE ops.lote_carga SET terminado_em = now(), linhas_lidas = %s, linhas_gravadas = %s, linhas_rejeitadas = %s, "
            "status = 'sucesso' WHERE lote_id = %s",
            (lidas, gravadas, len(rejeitadas), lote_id),
        )
    except Exception as e:  # noqa: BLE001 - registra e propaga
        conn.execute("UPDATE ops.lote_carga SET terminado_em = now(), status = 'falha', erro = %s WHERE lote_id = %s", (str(e)[:2000], lote_id))
        conn.commit()
        raise
    conn.commit()
    return {"lote_id": lote_id, "lidas": lidas, "gravadas": gravadas, "rejeitadas": len(rejeitadas)}


def _motivo_rejeicao(c: dict) -> str | None:
    if c.get("conversa_id") is None:
        return "sem_conversa_id"
    if not c.get("n_respostas_assistente"):
        return "sem_resposta_do_assistente"
    if c["ts_inicio"] > c["ts_fim"]:
        return "inicio_depois_do_fim"
    return None


def conferir_antes_de_publicar(linhas_por_semana: Sequence[tuple[str, int, int]], limite_desvios: float = 3.0) -> list[str]:
    """Alerta barato na própria carga (a reconciliação completa fica fora): salto de "novos" > 3 desvios da média de 8 semanas.
    `linhas_por_semana`: (semana, novos, user_agents_por_ip_maximo)."""
    alertas: list[str] = []
    historico: list[int] = []
    for semana, novos, _ in linhas_por_semana:
        base = historico[-8:]
        if len(base) >= 4:
            media = sum(base) / len(base)
            desvio = (sum((x - media) ** 2 for x in base) / len(base)) ** 0.5 or 1.0
            if abs(novos - media) > limite_desvios * desvio:
                alertas.append(f"{semana}: {novos} novos contra média de {media:.0f} nas semanas anteriores")
        historico.append(novos)
    return alertas


assert re.compile(r"^\d+\.\d+\.\d+$").match(VERSAO_DEFINICAO)
