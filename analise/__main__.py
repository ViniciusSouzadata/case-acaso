"""Uso:  python -m analise meta | eda | bruto | ajustado | semana | propensao | sensibilidade | validacao     (T-201..T-208). Os demais comandos entram nas tasks seguintes; `tudo` na T-209."""
from __future__ import annotations

import sys
import time
from datetime import date

import psycopg

from analise import achados, ajustado, bruto, eda, meta, propensao, semana, sensibilidade, validacao
from loader.migrar import dsn


def tudo() -> int:
    """Reexecuta toda a análise em ordem e regrava resultado.* (REQ-270). Semente fixa: duas execuções dão os mesmos números."""
    etapas = [["meta"], ["eda"], ["bruto"], ["ajustado"], ["semana"], ["propensao"], ["sensibilidade"]]
    if validacao.ROTULOS.is_file() and validacao.PREVISOES.is_file():
        etapas.append(["validacao"])
    etapas.append(["achados"])
    for e in etapas:
        t0 = time.time()
        if main(e) != 0:
            print(f"ERRO: etapa de análise '{e[0]}' falhou", file=sys.stderr)
            return 1
        print(f"[ok] análise: {e[0]:<14} {time.time() - t0:6.1f}s", flush=True)
    return 0


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
    if comando == "ajustado":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            linhas = ajustado.gravar(conn)
        n_aj = sum(1 for l in linhas if l["efeito_ajustado_pp"] is not None)
        print(f"resultado.efeito_fator: {len(linhas)} linhas, {n_aj} com efeito ajustado")
        return 0
    if comando == "semana":
        semanas = [date.fromisoformat(a) for a in argv[1:]] or None
        with psycopg.connect(dsn(), autocommit=True) as conn:
            for r in semana.gravar(conn, semanas):
                print(f"semana {r['semana']}: n={r['n_semana']} contra {r['n_base']}; delta {r['delta_pp']:+.1f} p.p. "
                      f"(mix {r['mix_pp']:+.1f}, taxa {r['taxa_pp']:+.1f}); p = {r['p_valor']:.3f}")
        return 0
    if comando == "propensao":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            linhas, balancos = propensao.gravar(conn)
        for l in linhas:
            ef = "não comparável" if l["efeito_ajustado_pp"] is None else (
                f"{l['efeito_ajustado_pp']:+.1f} p.p. ({l['ajustado_ic_inf']:+.1f} a {l['ajustado_ic_sup']:+.1f}); E-value {l['e_value']:.2f}")
            print(f"{l['fator']}: n={l['n_nivel']} × {l['n_referencia']}; pior balanço depois = {l['_pior_balanco']:.3f}; {ef}")
        print(f"resultado.balanco_propensao: {len(balancos)} linhas")
        return 0
    if comando == "sensibilidade":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            linhas = sensibilidade.gravar(conn)
        print(f"resultado.sensibilidade_efeito: {len(linhas)} linhas")
        return 0
    if comando == "validacao":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            for r in validacao.validar(conn, pesos=validacao.pesos_da_amostra()):
                print(f"validação de {r['classificador']}: n={r['n']}, acurácia {r['acuracia']:.3f}, kappa {r['kappa']:.3f} ({r['modelo']})")
        return 0
    if comando == "achados":
        with psycopg.connect(dsn(), autocommit=True) as conn:
            print(f"resultado.achado: {len(achados.gravar(conn))} achados")
        return 0
    if comando == "tudo":
        return tudo()
    print("uso: python -m analise meta | eda | bruto | ajustado | semana [AAAA-MM-DD ...] | propensao | sensibilidade | validacao | achados | tudo", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
