"""Uso:  python -m analise meta | eda | bruto     (T-201..T-203). Os demais comandos entram nas tasks seguintes; `tudo` na T-209."""
from __future__ import annotations

import sys

import psycopg

from analise import bruto, eda, meta
from loader.migrar import dsn


def main(argv: list[str]) -> int:
    comando = argv[0] if argv else ""
    if comando == "meta":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            m = meta.gravar(conn)
        print(f"resultado.meta gravada: n = {m['n_elegiveis']}, voltaram = {m['n_retornos']}, "
              f"taxa = {m['taxa_global']:.4f} (IC 95%: {m['ic_inf']:.4f} a {m['ic_sup']:.4f}); "
              f"efeito mínimo detectável {m['efeito_minimo_detectavel_pp']} p.p. (50/50) e "
              f"{m['efeito_minimo_detectavel_15_85_pp']} p.p. (15/85)")
        return 0
    if comando == "eda":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            r = eda.gerar(conn)
        print(f"EDA: {len(r['figuras'])} figuras ({', '.join(r['figuras'])}); {len(r['problemas'])} problemas de qualidade gravados")
        return 0
    if comando == "bruto":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            linhas = bruto.gravar(conn)
        print(f"resultado.efeito_fator (bruto): {len(linhas)} linhas, {len({l['fator'] for l in linhas})} fatores")
        return 0
    print("uso: python -m analise meta | eda | bruto", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
