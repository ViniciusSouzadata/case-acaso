"""Checagem do burn-in: retenção semanal das primeiras coortes com burn-in de 14 x 28 dias, e a semana 01/05/2023 refeita.

Só calcula ao lado: NÃO altera ops.parametros nem a definição v1.0.0. Só agregados (n e taxa); nenhum texto.
Uso (dentro do container do loader):  python scripts/burnin_14_vs_28.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import psycopg

from analise import semana as S
from analise.bruto import n_minimo
from loader.migrar import dsn

SQL = """
SELECT d.usuario_id, d.coorte_semana AS semana, d.ts_primeira, d.maduro, d.trafego_anomalo,
       f.dispositivo, f.modelo_familia, f.voltou_7d,
       (SELECT min(ts_inicio) FROM stg.conversa) AS base_ini
FROM mart.dim_usuario d JOIN mart.fct_primeira_experiencia f USING (usuario_id)
WHERE d.maduro AND NOT d.trafego_anomalo
"""


def main() -> int:
    with psycopg.connect(dsn(), autocommit=True) as conn:
        cur = conn.execute(SQL)
        df = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
        n_min = n_minimo(conn)
    df["voltou_7d"] = df["voltou_7d"].astype(bool)
    corte = {d: df[df["ts_primeira"] >= df["base_ini"] + pd.Timedelta(days=d)] for d in (14, 28)}
    for d, x in corte.items():
        print(f"burn-in {d} d: elegíveis {len(x)}, voltaram {int(x['voltou_7d'].sum())}, taxa {x['voltou_7d'].mean():.4f}")
    semanas = sorted(corte[14]["semana"].unique())[:8]
    print("\nsemana      | 14d: n  taxa  | 28d: n  taxa")
    for s in semanas:
        l = []
        for d in (14, 28):
            x = corte[d][corte[d]["semana"] == s]
            l.append(f"{len(x):4d}  {x['voltou_7d'].mean()*100:5.1f}%" if len(x) else "   0      -")
        print(f"{s:%d/%m/%Y} | {l[0]} | {l[1]}")
    print("\n01/05/2023 refeita")
    for d in (14, 28):
        x = corte[d].copy()
        try:
            r, _ = S.decompor(x, date(2023, 5, 1), n_min)
            print(f"burn-in {d} d: base n={r['n_base']} taxa={r['taxa_base']:.4f} | semana n={r['n_semana']} taxa={r['taxa_semana']:.4f} "
                  f"| delta {r['delta_pp']:.1f} (mix {r['mix_pp']:.1f} / taxa {r['taxa_pp']:.1f}) p={r['p_valor']:.3f} | {r['base_descricao']}")
        except ValueError as e:
            print(f"burn-in {d} d: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
