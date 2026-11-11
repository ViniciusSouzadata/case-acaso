"""Subida ponta a ponta (T-110): migrar -> verificar o bruto (ou extrair) -> carregar -> transformar -> reconciliar.

Uso:  python -m loader.cli
  FULL_REFRESH=1  em vez de só verificar o snapshot, baixa o WildChat-1M completo e reextrai (lento).

Cada etapa imprime uma linha com nome e duração. Qualquer falha encerra com código 1 e diz qual etapa quebrou.
No fim, um resumo de uma tela só com agregados (nunca conteúdo de conversa).
"""
from __future__ import annotations

import os
import sys
import time

import psycopg

from loader import carregar, extrair, migrar, reconciliar, transformar
from loader.migrar import dsn


class EtapaFalhou(Exception):
    def __init__(self, etapa: str, causa: Exception):
        super().__init__(f"etapa '{etapa}' falhou: {type(causa).__name__}: {causa}")
        self.etapa = etapa


def _etapa(nome: str, fn):
    t0 = time.time()
    try:
        r = fn()
    except Exception as e:  # noqa: BLE001 - qualquer falha vira "etapa X falhou"
        raise EtapaFalhou(nome, e) from e
    print(f"[ok] {nome:<22} {time.time() - t0:6.1f}s", flush=True)
    return r


def _bruto():
    if os.environ.get("FULL_REFRESH") == "1":
        extrair.extrair_completo()
    extrair.verificar_snapshot(extrair.SNAPSHOT)


def _resumo(carga: dict, linhas_reconc: list[tuple], total: float) -> str:
    with psycopg.connect(dsn(), autocommit=True) as c:
        um = lambda q: c.execute(q).fetchone()  # noqa: E731
        n_conv = um("SELECT count(*) FROM stg.conversa")[0]
        n_usr = um("SELECT count(*) FROM mart.dim_usuario")[0]
        o = um("SELECT usuarios, voltaram_7d, taxa, ic_inf, ic_sup FROM mart.agg_retencao_sensibilidade "
               "WHERE definicao = 'oficial'")
    ok = sum(1 for l in linhas_reconc if l[-1])
    pct = lambda x: f"{float(x) * 100:.2f}%".replace(".", ",")  # noqa: E731
    return "\n".join([
        "=" * 64,
        "RESUMO DA SUBIDA",
        f"  conversas na base ........ {n_conv:,}".replace(",", "."),
        f"  usuários (definição v1) .. {n_usr:,}".replace(",", "."),
        f"  elegíveis ................ {o[0]:,}".replace(",", "."),
        f"  voltaram em 7 dias ....... {o[1]:,}".replace(",", "."),
        f"  taxa oficial ............. {pct(o[2])}  (IC 95%: {pct(o[3])} a {pct(o[4])}; n = {o[0]})",
        f"  linhas rejeitadas ........ {carga['rejeitadas']}",
        f"  reconciliação ............ {'OK' if ok == len(linhas_reconc) else 'DIVERGE'} "
        f"({ok}/{len(linhas_reconc)} métricas com diferença dentro da tolerância)",
        f"  tempo total .............. {total:.1f}s",
        "=" * 64,
    ])


def main() -> int:
    t0 = time.time()
    try:
        _etapa("migrar", migrar.migrar)
        _etapa("extrair" if os.environ.get("FULL_REFRESH") == "1" else "verificar bruto", _bruto)
        carga = _etapa("carregar", carregar.carregar)
        _etapa("transformar", transformar.transformar)
        linhas = _etapa("reconciliar", reconciliar.reconciliar)
        print(_resumo(carga, linhas, time.time() - t0))
    except EtapaFalhou as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 - falha no resumo
        print(f"ERRO: resumo: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
