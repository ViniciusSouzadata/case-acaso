"""T-501: consulta de confirmação do incidente §4.2, rodável no bruto (DuckDB sobre o snapshot).

Mostra, com dado real, o mecanismo: a chave `hashed_ip|user-agent` (a do código de referência) gera mais "usuários novos"
que a chave `hashed_ip`, e quase todos os "novos" a mais caem em IP que já existia. Só agregados; nada de conversa, IP ou UA na saída.

Uso:  PYTHONUTF8=1 python scripts/incidente_confirmacao.py [snapshot.parquet] [saida.md]
Mesma lógica em Postgres: docs/incidente/confirmacao.sql (roda sobre stg.conversa).
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"
SAIDA = RAIZ / "docs" / "incidente" / "evidencia.md"
FUSO = "America/Sao_Paulo"

# Uma linha por conversa: IP, UA e INÍCIO da conversa. No snapshot o turno do usuário vem sem horário; o início é o da 1ª resposta
# do assistente (mesma regra do loader, `ts_inicio`). O código de referência usa o último turno: defeito tratado na T-502.
BASE = """
CREATE OR REPLACE TEMP VIEW conv AS
SELECT hashed_ip AS ip,
       coalesce(header."user-agent", '') AS ua,
       coalesce(conversation[1]."timestamp", conversation[2]."timestamp") AS t
FROM read_parquet('{snapshot}')
WHERE country = 'Brazil' AND hashed_ip IS NOT NULL
  AND coalesce(conversation[1]."timestamp", conversation[2]."timestamp") IS NOT NULL;  -- sem resposta do assistente: rejeitada na carga

-- primeira aparição de cada chave
CREATE OR REPLACE TEMP VIEW chave_ip_ua AS SELECT ip, ua, min(t) AS t0 FROM conv GROUP BY ip, ua;
CREATE OR REPLACE TEMP VIEW chave_ip    AS SELECT ip, min(t) AS t0 FROM conv GROUP BY ip;
"""

POR_SEMANA = f"""
WITH k AS (
  SELECT c.ip, c.ua, c.t0, i.t0 AS t0_ip,
         date_trunc('week', timezone('{FUSO}', c.t0))::date AS semana
  FROM chave_ip_ua c JOIN chave_ip i USING (ip)
), ip_novos AS (
  SELECT date_trunc('week', timezone('{FUSO}', t0))::date AS semana, count(*) AS novos_ip FROM chave_ip GROUP BY 1
), ip_ua_novos AS (
  SELECT semana, count(*) AS novos_ip_ua,
         count(*) FILTER (WHERE t0_ip < t0) AS novos_em_ip_ja_visto
  FROM k GROUP BY 1
), max_ua AS (
  SELECT semana, max(n) AS max_uas_novos_por_ip FROM (SELECT semana, ip, count(*) AS n FROM k GROUP BY 1, 2) GROUP BY 1
)
SELECT semana, coalesce(novos_ip, 0) AS novos_ip, novos_ip_ua, novos_em_ip_ja_visto, max_uas_novos_por_ip
FROM ip_ua_novos LEFT JOIN ip_novos USING (semana) JOIN max_ua USING (semana)
ORDER BY semana
"""

TOTAIS = """
SELECT (SELECT count(*) FROM chave_ip) AS usuarios_ip,
       (SELECT count(*) FROM chave_ip_ua) AS usuarios_ip_ua,
       (SELECT max(n) FROM (SELECT count(*) AS n FROM chave_ip_ua GROUP BY ip)) AS max_uas_por_ip
"""


def calcular(snapshot: Path = SNAPSHOT) -> dict:
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    for cmd in BASE.format(snapshot=str(snapshot).replace("\\", "/")).split(";"):
        if cmd.strip():
            con.execute(cmd)
    usuarios_ip, usuarios_ip_ua, max_uas = con.execute(TOTAIS).fetchall()[0]
    colunas = ["semana", "novos_ip", "novos_ip_ua", "novos_em_ip_ja_visto", "max_uas_novos_por_ip"]
    semanas = [dict(zip(colunas, l)) for l in con.execute(POR_SEMANA).fetchall()]
    return {"usuarios_ip": usuarios_ip, "usuarios_ip_ua": usuarios_ip_ua, "max_uas_por_ip": max_uas, "semanas": semanas}


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _pct(a: float, b: float) -> str:
    return f"{100 * (a / b - 1):+.1f}%".replace(".", ",")


def relatorio(r: dict) -> str:
    n_ip, n_ua = r["usuarios_ip"], r["usuarios_ip_ua"]
    ja_visto = sum(s["novos_em_ip_ja_visto"] for s in r["semanas"])
    linhas = [
        "# Incidente §4.2: evidência do mecanismo no dado real (WildChat Brasil)",
        "",
        "Gerado por `scripts/incidente_confirmacao.py` sobre o snapshot; só agregados.",
        "",
        "## Resumo",
        f"- Usuários pela chave `hashed_ip`: **{_milhar(n_ip)}**",
        f"- Usuários pela chave `hashed_ip|user-agent` (a do código de referência): **{_milhar(n_ua)}** ({_pct(n_ua, n_ip)})",
        f"- Dos {_milhar(n_ua)} \"novos\" pela chave IP+UA, **{_milhar(ja_visto)}** caem em um IP que já tinha aparecido antes "
        "(mesma pessoa ou mesmo lugar, outro navegador)",
        f"- Máximo de user-agents diferentes em um único IP: **{r['max_uas_por_ip']}**",
        "",
        "## Por semana (semana no fuso de São Paulo, início da conversa)",
        "| Semana | Novos por IP | Novos por IP+UA | Dos novos IP+UA, em IP já visto | Máx. UAs novos num IP |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in r["semanas"]:
        linhas.append(f"| {s['semana']:%d/%m/%Y} | {s['novos_ip']} | {s['novos_ip_ua']} | {s['novos_em_ip_ja_visto']} | {s['max_uas_novos_por_ip']} |")
    linhas += [
        "",
        "## Como ler",
        "A chave com user-agent conta como \"novo\" quem só trocou de navegador ou de versão, e conta cada navegador de um mesmo IP "
        "como uma pessoa. Isso infla o denominador da retenção (novos), enquanto o numerador (quem voltou) quase não muda: é o "
        "padrão do incidente. Os números do case (1.210 novos por semana) não existem neste dado; aqui se mostra o mecanismo.",
        "",
    ]
    return "\n".join(linhas)


def main(argv: list[str]) -> int:
    snapshot = Path(argv[0]) if argv else SNAPSHOT
    saida = Path(argv[1]) if len(argv) > 1 else SAIDA
    r = calcular(snapshot)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(relatorio(r), encoding="utf-8")
    print(f"usuários: IP {r['usuarios_ip']} x IP+UA {r['usuarios_ip_ua']}; máx UAs por IP {r['max_uas_por_ip']}; {len(r['semanas'])} semanas; gravado em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
