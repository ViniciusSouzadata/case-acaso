"""Robustez do efeito da recusa na 1ª resposta (R1–R5). Só agregados; nenhum texto, IP ou user-agent é impresso ou gravado.

R1 efeito ajustado nas 4 definições da sensibilidade e com burn-in de 28 dias (só ao lado; o oficial não muda)
R2 recusa × tema: n de recusas por tema e efeito bruto (Newcombe) dentro dos temas com mais recusas
R3 concentração por IP: IPs distintos nas recusas, o maior e o efeito ajustado sem os 10 IPs com mais recusas
R4 erro do classificador (não diferencial): correção simples de atenuação com precisão/revocação ponderadas da validação
R5 a mesma tabela com a recusa por REGRAS nos mesmos usuários (o −3,2 de antes)

Uso: python scripts/robustez_recusa.py   (precisa do banco; escreve docs/robustez_recusa.md)
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import numpy as np
import pandas as pd
import psycopg

from analise import sensibilidade as S
from analise import validacao as V
from analise.ajustado import ajustar
from analise.bruto import n_minimo
from analise.intervalos import newcombe
from loader.derivar import detectar_recusa
from loader.migrar import dsn

PRECISAO_POND, REVOCACAO_POND = 0.811, 0.861   # Haiku 5.5, recusa, ponderadas pelo tamanho do estrato (docs/validacao_llm.md)


def efeito_recusa(df: pd.DataFrame, grupos: np.ndarray, n_min: int) -> dict:
    linhas, _ = ajustar(df, pd.Series(grupos), n_min)
    l = next(x for x in linhas if x["fator"] == "recusa")
    return {"ame": l["efeito_ajustado_pp"], "inf": l["ajustado_ic_inf"], "sup": l["ajustado_ic_sup"], "p": l["p_valor"]}


def bruto_recusa(df: pd.DataFrame, rec: pd.Series) -> dict:
    k1, n1 = int(df.loc[rec, "voltou_7d"].sum()), int(rec.sum())
    k0, n0 = int(df.loc[~rec, "voltou_7d"].sum()), int((~rec).sum())
    d, inf, sup = newcombe(k1, n1, k0, n0)
    return {"n1": n1, "n0": n0, "taxa1": k1 / n1 if n1 else float("nan"), "taxa0": k0 / n0 if n0 else float("nan"),
            "bruto": d * 100, "inf": inf * 100, "sup": sup * 100}


def corrigir_atenuacao(obs_rec: float, obs_non: float, prevalencia_obs: float, ppv: float, sens: float) -> tuple[float, float]:
    """Retorna (r1, r0): taxa de retorno de quem de fato recusou / de quem não, supondo erro não diferencial.

    rotulado sim: obs_rec = ppv*r1 + (1-ppv)*r0 ;  rotulado não: obs_non = (1-npv_f)*r0 + npv_f*r1, com npv_f = P(recusa real | rótulo não).
    """
    pi = prevalencia_obs * ppv / sens                      # prevalência real implícita
    fn = pi * (1 - sens) / (1 - prevalencia_obs)           # P(recusa real | rótulo não)
    a = np.array([[ppv, 1 - ppv], [fn, 1 - fn]])
    r1, r0 = np.linalg.solve(a, np.array([obs_rec, obs_non]))
    return float(r1), float(r0)


def main() -> int:
    saida = []
    p = lambda s="": (print(s), saida.append(s))  # noqa: E731
    with psycopg.connect(dsn(), autocommit=True) as conn:
        conv, par, eras = S.carregar(conn)
        n_min = n_minimo(conn)
    p("# Robustez do efeito da recusa (R1–R5)\n\nGerado por `scripts/robustez_recusa.py`. Só agregados.\n")

    # R1 ------------------------------------------------------------------------------------------
    p("## R1 — Efeito ajustado da recusa por definição\n\n| Definição | n | recusas | efeito ajustado (p.p.) | IC 95% | p |\n|---|---:|---:|---:|---|---:|")
    base = {}
    for nome, chave, gap in S.DEFINICOES + [("burn-in 28 dias", "usuario_id", None)]:
        pr = {**par, "burn_in_dias": 28} if nome.startswith("burn-in") else par
        df, grupos = S.reconstruir(conv, chave, gap or par["gap_sessao_min"], pr, eras)
        e = efeito_recusa(df, grupos, n_min)
        base[nome] = (df, grupos)
        p(f"| {nome} | {len(df)} | {int(df['recusa'].sum())} | {e['ame']:+.1f} | {e['inf']:+.1f} a {e['sup']:+.1f} | {e['p']:.4f} |")
    df, grupos = base["oficial"]

    # R2 ------------------------------------------------------------------------------------------
    p("\n## R2 — Recusa × tema (definição oficial)\n\n| Tema (LLM) | n | recusas | % recusa | retorno com recusa | retorno sem recusa | efeito bruto (p.p.) | IC 95% (Newcombe) |\n|---|---:|---:|---:|---:|---:|---:|---|")
    rec = df["recusa"].astype(bool)
    por_tema = df.assign(rec=rec).groupby("tema").agg(n=("rec", "size"), r=("rec", "sum")).sort_values("r", ascending=False)
    for tema, row in por_tema.iterrows():
        sub = df["tema"] == tema
        if row["r"] >= 10 and (~rec[sub]).sum() >= 10:
            b = bruto_recusa(df[sub], rec[sub])
            p(f"| {tema} | {row['n']} | {int(row['r'])} | {row['r'] / row['n'] * 100:.1f}% | {b['taxa1'] * 100:.1f}% | {b['taxa0'] * 100:.1f}% | "
              f"{b['bruto']:+.1f} | {b['inf']:+.1f} a {b['sup']:+.1f} |")
        else:
            p(f"| {tema} | {row['n']} | {int(row['r'])} | {row['r'] / row['n'] * 100:.1f}% | (poucas recusas) | | | |")
    p("\nNota: o modelo ajustado de R1 já inclui o tema como covariável.")

    # R3 ------------------------------------------------------------------------------------------
    por_ip = pd.Series(grupos[rec.to_numpy()]).value_counts()
    top10 = set(por_ip.index[:10])
    manter = ~pd.Series(grupos).isin(top10).to_numpy()
    e3 = efeito_recusa(df[manter].reset_index(drop=True), grupos[manter], n_min)
    p(f"\n## R3 — Concentração por IP\n\n- Recusas: {int(rec.sum())}; IPs distintos com recusa: {len(por_ip)}; maior IP: {int(por_ip.iloc[0])} recusas; "
      f"os 10 maiores somam {int(por_ip.iloc[:10].sum())}.\n- Efeito ajustado sem os 10 IPs com mais recusas (n = {int(manter.sum())}, "
      f"recusas = {int(rec[manter].sum())}): {e3['ame']:+.1f} p.p. (IC {e3['inf']:+.1f} a {e3['sup']:+.1f}; p = {e3['p']:.4f}).")

    # R4 ------------------------------------------------------------------------------------------
    b = bruto_recusa(df, rec)
    r1, r0 = corrigir_atenuacao(b["taxa1"], b["taxa0"], rec.mean(), PRECISAO_POND, REVOCACAO_POND)
    p(f"\n## R4 — Erro do classificador (não diferencial)\n\n- Precisão ponderada {PRECISAO_POND}, revocação ponderada {REVOCACAO_POND} (validação nas 200).\n"
      f"- Retorno observado: rotulado recusa {b['taxa1'] * 100:.1f}%, rotulado não-recusa {b['taxa0'] * 100:.1f}% (bruto {b['bruto']:+.1f} p.p.).\n"
      f"- Corrigindo a mistura (cada grupo rotulado mistura os dois tipos reais): retorno de quem de fato recusou {r1 * 100:.1f}%, "
      f"de quem não {r0 * 100:.1f}% → diferença {((r1 - r0) * 100):+.1f} p.p.; fator de correção {((r1 - r0) / (b['taxa1'] - b['taxa0'])):.2f}×.\n"
      f"- Leitura: erro de classificação que não depende do desfecho **encolhe** o efeito em direção a zero; o efeito observado tende a ser um limite inferior em módulo. "
      f"Vale só se o erro for não diferencial: se o LLM errar mais em quem some (por exemplo, recusa suave em pedido difícil), o viés pode ir para qualquer lado.")

    # R5 ------------------------------------------------------------------------------------------
    _, padroes = V._padroes_recusa()
    ids = set(df["conversa_id"].astype(int))
    regras = {}
    for cid, _m, resposta in V._conversas_do_bruto(V.SNAPSHOT):
        if cid in ids:
            regras[cid] = bool(detectar_recusa(resposta, padroes))
    df_r = df.copy()
    df_r["recusa"] = df_r["conversa_id"].astype(int).map(regras).astype(bool)
    er = efeito_recusa(df_r, grupos, n_min)
    br = bruto_recusa(df_r, df_r["recusa"])
    cruz = pd.crosstab(rec.to_numpy(), df_r["recusa"].to_numpy())
    p(f"\n## R5 — Recusa por regras nos mesmos {len(df)} usuários\n\n| Rótulo | recusas | retorno com recusa | retorno sem | bruto (p.p.) | IC Newcombe | ajustado (p.p.) | IC 95% | p |\n|---|---:|---:|---:|---:|---|---:|---|---:|\n"
      f"| LLM (Haiku 5.5) | {int(rec.sum())} | {b['taxa1'] * 100:.1f}% | {b['taxa0'] * 100:.1f}% | {b['bruto']:+.1f} | {b['inf']:+.1f} a {b['sup']:+.1f} | "
      f"{efeito_recusa(df, grupos, n_min)['ame']:+.1f} | ver R1 | |\n"
      f"| Regras | {br['n1']} | {br['taxa1'] * 100:.1f}% | {br['taxa0'] * 100:.1f}% | {br['bruto']:+.1f} | {br['inf']:+.1f} a {br['sup']:+.1f} | "
      f"{er['ame']:+.1f} | {er['inf']:+.1f} a {er['sup']:+.1f} | {er['p']:.4f} |")
    both = int(cruz.loc[True, True]) if (True in cruz.index and True in cruz.columns) else 0
    p(f"\nConcordância: as duas marcam {both}; só LLM {int(rec.sum()) - both}; só regras {br['n1'] - both}.")
    (RAIZ / "docs" / "robustez_recusa.md").write_text("\n".join(saida) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
