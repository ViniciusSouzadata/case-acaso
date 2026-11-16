"""Alerta de divergência (docs/entrega.md, seção 7).

Três regras, todas sobre AGREGADOS (nunca texto de conversa, IP ou user-agent):
  1. reconciliação: alguma métrica de ops.reconciliacao do último lote fora da tolerância;
  2. salto de "pessoas novas" por semana acima de N desvios da média das semanas anteriores (só semanas maduras);
  3. salto do máximo de user-agents por IP por semana, pela mesma regra.
O número de desvios, a janela, o histórico mínimo e quantas semanas finais avaliar vêm de ops.parametros
(alerta_desvios, alerta_janela_semanas, alerta_min_historico, alerta_semanas_avaliadas); nada disso está escrito aqui.
O desvio usado tem piso na raiz da média (ruído natural de uma contagem), para contagens pequenas não alarmarem à toa. Semanas do início da coleta (BDR-09) ficam fora da regra 2.

O aviso sai em texto na saída padrão (e, se ALERTA_ARQUIVO estiver definido, é anexado a esse arquivo). Não há canal
externo (e-mail, chat) ligado: isso exigiria credencial e fica declarado como não feito.

Uso:
  python -m loader.alerta           confere o banco (último lote)
  python -m loader.alerta --historico  avalia todas as semanas da série (retrospectiva, para medir falso alarme)
  python -m loader.alerta --demo    roda com séries inventadas, sem banco e sem credencial
Código de saída: 0 sem alerta, 2 com alerta (para a esteira poder barrar).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Limiares:
    desvios: float
    janela: int
    min_historico: int
    avaliadas: int = 1   # quantas semanas finais da série avaliar; 0 = todas (retrospectiva)


@dataclass(frozen=True)
class Alerta:
    regra: str      # "reconciliacao" | "novos_por_semana" | "uas_por_ip"
    detalhe: str    # só números e nomes de métrica


def detectar_saltos(
    serie: Sequence[tuple[str, float]], lim: Limiares, regra: str, rotulo: str
) -> list[Alerta]:
    """serie: (semana, valor) em ordem cronológica. Salto = |valor - média| > desvios × desvio-padrão das `janela`
    semanas anteriores (precisa de `min_historico`). O desvio tem piso na raiz da média (ruído de contagem) e em 1.
    Avalia só as `lim.avaliadas` últimas semanas (0 = todas)."""
    alertas: list[Alerta] = []
    inicio = 0 if lim.avaliadas <= 0 else max(0, len(serie) - lim.avaliadas)
    for i, (semana, valor) in enumerate(serie):
        if i < inicio:
            continue
        base = [v for _, v in serie[max(0, i - lim.janela):i]]
        if len(base) < lim.min_historico:
            continue
        media = sum(base) / len(base)
        desvio = max((sum((v - media) ** 2 for v in base) / len(base)) ** 0.5, max(media, 0.0) ** 0.5, 1.0)
        if abs(valor - media) > lim.desvios * desvio:
            alertas.append(Alerta(regra, f"{semana}: {rotulo} {valor:g} contra média de {media:.1f} "
                                         f"nas {len(base)} semanas anteriores (limite: {lim.desvios:g} desvios, desvio {desvio:.1f})"))
    return alertas


def avaliar_reconciliacao(linhas: Sequence[tuple[str, float, float, bool]]) -> list[Alerta]:
    """linhas: (metrica, valor_bruto, valor_mart, ok). Alerta por métrica com ok = false."""
    return [Alerta("reconciliacao", f"{m}: origem {b:g} contra base {t:g}") for m, b, t, ok in linhas if not ok]


def montar_aviso(alertas: Sequence[Alerta]) -> str:
    if not alertas:
        return "ALERTA: nenhum. Reconciliação dentro da tolerância e séries semanais dentro da variação normal."
    linhas = [f"ALERTA: {len(alertas)} divergência(s) acima da variação normal."]
    linhas += [f"- [{a.regra}] {a.detalhe}" for a in alertas]
    return "\n".join(linhas)


def avaliar(
    reconc: Sequence[tuple[str, float, float, bool]],
    novos: Sequence[tuple[str, float]],
    uas_por_ip: Sequence[tuple[str, float]],
    lim: Limiares,
) -> list[Alerta]:
    return (
        avaliar_reconciliacao(reconc)
        + detectar_saltos(novos, lim, "novos_por_semana", "novos")
        + detectar_saltos(uas_por_ip, lim, "uas_por_ip", "máx. de user-agents por IP")
    )


# --------------------------------------------------------------------------------------------------- banco
def _ler_do_banco(historico: bool = False) -> tuple[Limiares, list, list, list]:
    import psycopg  # noqa: PLC0415 - só o modo banco precisa

    from loader.migrar import dsn  # noqa: PLC0415

    with psycopg.connect(dsn()) as conn:
        p = dict(conn.execute("SELECT chave, valor FROM ops.parametros WHERE chave LIKE 'alerta_%%'").fetchall())
        lim = Limiares(float(p["alerta_desvios"]), int(p["alerta_janela_semanas"]), int(p["alerta_min_historico"]),
                      0 if historico else int(p["alerta_semanas_avaliadas"]))
        reconc = [
            (m, float(b), float(t), bool(ok))
            for m, b, t, ok in conn.execute(
                "SELECT metrica, valor_bruto, valor_mart, ok FROM ops.reconciliacao "
                "WHERE lote_id = (SELECT max(lote_id) FROM ops.reconciliacao) ORDER BY metrica"
            )
        ]
        novos = [
            (str(per), float(n))
            for per, n in conn.execute(
                "SELECT periodo, novos FROM mart.agg_retencao_periodo "
                "WHERE granularidade = 'semana' AND NOT inicio_coleta AND madura ORDER BY periodo"
            )
        ]
        uas = [
            (str(sem), float(n))
            for sem, n in conn.execute(
                "SELECT sem, max(n) FROM ("
                "  SELECT (date_trunc('week', ts_inicio AT TIME ZONE ops.param('fuso_pais')))::date AS sem, "
                "         count(DISTINCT user_agent) AS n FROM stg.conversa GROUP BY 1, hashed_ip) t "
                "GROUP BY sem ORDER BY sem"
            )
        ]
    return lim, reconc, novos, uas


def _demo() -> tuple[Limiares, list, list, list]:
    """Séries inventadas: 12 semanas estáveis e um salto de 'novos' e de user-agents na 11ª; uma métrica divergente."""
    lim = Limiares(desvios=3.0, janela=8, min_historico=4, avaliadas=0)  # só na demonstração; no banco vêm de ops.parametros
    base_novos = [100, 104, 98, 101, 99, 103, 97, 102, 100, 101]
    novos = [(f"2023-S{i + 1:02d}", float(v)) for i, v in enumerate(base_novos + [210, 102])]
    uas = [(f"2023-S{i + 1:02d}", float(v)) for i, v in enumerate([2, 3, 2, 2, 3, 2, 3, 2, 2, 3, 35, 3])]
    reconc = [("conversas_aceitas", 1000.0, 1000.0, True), ("usuarios_oficiais", 2372.0, 2400.0, False)]
    return lim, reconc, novos, uas


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    lim, reconc, novos, uas = _demo() if "--demo" in args else _ler_do_banco("--historico" in args)
    aviso = montar_aviso(avaliar(reconc, novos, uas, lim))
    print(aviso)
    destino = os.environ.get("ALERTA_ARQUIVO")
    if destino:
        with Path(destino).open("a", encoding="utf-8") as f:
            f.write(aviso + "\n")
    return 0 if aviso.startswith("ALERTA: nenhum") else 2


if __name__ == "__main__":
    raise SystemExit(main())
