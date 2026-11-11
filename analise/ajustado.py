"""T-204: efeito ajustado = regressão logística de voltou_7d + efeito marginal médio (em p.p.) com IC pelo método delta.

- Modelo: fatores de assistente + perfil + era de modelo (engajamento fica FORA: turnos acontecem depois da resposta).
- Erro-padrão agrupado por IP (usuários do mesmo IP não são independentes). O IP só existe em memória, como código.
- Efeito marginal médio de um nível = média, sobre a população, de P(voltou | nível) - P(voltou | referência).
- p-valores do efeito marginal corrigidos por Benjamini-Hochberg a 5%.
- Limite de ~25 parâmetros (566 retornos): níveis com menos de n_minimo usuários saem do modelo (juntados à referência).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import psycopg
import statsmodels.api as sm
from scipy.stats import norm

from analise.bruto import COLUNAS_BRUTO, calcular_bruto, n_minimo
from analise.dados import carregar_elegiveis, carregar_grupos_ip
from analise.fatores import ENGAJAMENTO, FATORES, FAIXA_PERGUNTA_CURTA, Fator, agrupar_raros
from analise.gravar import substituir

MAX_PARAMETROS = 25  # sem contar o intercepto
FDR = 0.05
Z = 1.96

COLUNAS_AJUSTADO = [
    "efeito_ajustado_pp", "ajustado_ic_inf", "ajustado_ic_sup", "p_valor", "significativo_fdr", "e_value",
    "leitura", "ordem",
]
COLUNAS_EFEITO = COLUNAS_BRUTO + COLUNAS_AJUSTADO

ROTULOS = {
    "recusa": "recusa na 1ª resposta", "idioma_divergente": "resposta em idioma diferente do da pergunta (pergunta com mais de 30 caracteres)",
    "faixa_chars_resposta": "tamanho da resposta", "modelo_familia": "modelo", "tema": "tema", "idioma": "idioma da pergunta",
    "dispositivo": "dispositivo", "periodo_dia": "período do dia", "fim_de_semana": "fim de semana",
    "faixa_chars_pergunta": "tamanho da pergunta", "regiao": "região", "era_modelo": "era de oferta de modelo",
    "n_turnos_sessao": "turnos na sessão", "n_conversas_sessao": "conversas na sessão",
}


@dataclass
class Plano:
    """Matriz de desenho do modelo e o que foi decidido para montá-la (registrado, nunca silencioso)."""
    X: pd.DataFrame
    colunas_nivel: dict[tuple[str, str], str]            # (fator, nível) -> coluna da matriz
    referencias: dict[str, str]
    populacao_ame: dict[str, pd.Series]                 # fator -> máscara das linhas em que o efeito é definido
    notas: list[str] = field(default_factory=list)
    n_parametros: int = 0


# ----------------------------------------------------------------------------------------------- regras puras
def benjamini_hochberg(p: list[float], q: float = FDR) -> list[bool]:
    """Quais hipóteses sobrevivem ao controle de taxa de falsa descoberta q (Benjamini-Hochberg), na ordem de entrada."""
    m = len(p)
    if m == 0:
        return []
    ordem = sorted(range(m), key=lambda i: p[i])
    corte = -1
    for pos, i in enumerate(ordem, start=1):
        if p[i] <= q * pos / m:
            corte = pos
    passa = [False] * m
    for pos, i in enumerate(ordem, start=1):
        passa[i] = pos <= corte
    return passa


def _por_100(x: float) -> str:
    """Pontos percentuais como 'a cada 100' em linguagem simples: 1 casa abaixo de 10, inteiro acima."""
    x = abs(x)
    return (f"{x:.1f}" if x < 10 else f"{x:.0f}").replace(".", ",")


def _faixa_por_100(inf: float, sup: float) -> str:
    def f(x):
        return ("+" if x > 0 else "−" if x < 0 else "") + _por_100(x)
    return f"entre {f(inf)} e {f(sup)} a cada 100"


def leitura_efeito(fator: str, nivel: str, referencia: str, efeito: float, inf: float, sup: float, ajustado: bool = True,
                   sobrevive_fdr: bool | None = None) -> str:
    """Frase para o cliente, sem jargão. Intervalo que cruza zero = 'não dá para afirmar diferença' (nunca vende ruído como efeito).

    `sobrevive_fdr` False com intervalo fora de zero: avisa que, com tantos fatores comparados, pode ser acaso.
    """
    rot = ROTULOS.get(fator, fator)
    faixa = _faixa_por_100(inf, sup)
    if not ajustado:
        base = (f"{rot}: quem teve '{nivel}' voltou {_por_100(efeito)} a cada 100 {'a mais' if efeito > 0 else 'a menos'} do que quem teve "
                f"'{referencia}'" if not inf <= 0 <= sup else
                f"{rot}: entre quem teve '{nivel}' e quem teve '{referencia}' não dá para afirmar diferença no retorno")
        return base + " (só descrição: isso acontece depois da primeira resposta, então não mostra o que fez a pessoa voltar)."
    comparacao = f"'{nivel}' contra '{referencia}', depois de levar em conta o perfil de quem chegou"
    if inf <= 0 <= sup:
        return (f"{rot}: {comparacao}, não dá para afirmar diferença: com esta quantidade de usuários, "
                f"o que se vê ({faixa}) pode ser só acaso.")
    sentido = "a mais" if efeito > 0 else "a menos"
    texto = (f"{rot}: {comparacao}, voltaram cerca de {_por_100(efeito)} a cada 100 {sentido} "
             f"(o valor real deve estar {faixa}).")
    if sobrevive_fdr is False:
        texto += " Como foram comparados muitos fatores ao mesmo tempo, uma diferença assim pode aparecer por acaso."
    return texto


# ----------------------------------------------------------------------------------------------- modelo
def montar_plano(df: pd.DataFrame, n_min: int, fatores: list[Fator] | None = None) -> Plano:
    """Matriz de desenho: um conjunto de dummies por fator (assistente + perfil), referência = nível mais frequente."""
    cols: dict[str, pd.Series] = {}
    mapa: dict[tuple[str, str], str] = {}
    refs: dict[str, str] = {}
    pops: dict[str, pd.Series] = {}
    notas: list[str] = []
    for f in fatores or FATORES:
        if f.grupo == ENGAJAMENTO:
            continue
        nivel = f.preparar(df)
        valido = nivel.notna()
        if f.nome == "idioma_divergente":
            # decisão do planejador: dummy = divergente E pergunta > 30 chars (0 para as curtas, absorvidas pela faixa de tamanho da pergunta)
            nivel = nivel.where(valido, "não")
            pops[f.nome] = valido
        else:
            pops[f.nome] = pd.Series(True, index=df.index)
        nivel = agrupar_raros(nivel[nivel.notna()], n_min).reindex(df.index)
        n = nivel.value_counts()
        if len(n) < 2:
            continue
        ref = min(n.index, key=lambda x: (-n[x], str(x)))
        for nv in sorted(n.index, key=str):
            if nv != ref and n[nv] < n_min:
                notas.append(f"{f.nome}: nível '{nv}' (n={int(n[nv])}) abaixo do mínimo; juntado à referência '{ref}' e fora do modelo")
                nivel = nivel.where(nivel != nv, ref)
        n = nivel.value_counts()
        if len(n) < 2:
            continue
        refs[f.nome] = ref
        for nv in sorted(n.index, key=str):
            if nv == ref:
                continue
            nome_col = f"{f.nome}::{nv}"
            cols[nome_col] = (nivel == nv).astype(float)
            mapa[(f.nome, str(nv))] = nome_col
    X = pd.DataFrame(cols, index=df.index)
    X.insert(0, "const", 1.0)
    return Plano(X=X, colunas_nivel=mapa, referencias=refs, populacao_ame=pops, notas=notas, n_parametros=X.shape[1] - 1)


def _ame(res, X: pd.DataFrame, coluna: str, outras_do_fator: list[str], linhas: pd.Series) -> tuple[float, float]:
    """(efeito marginal médio, erro-padrão pelo método delta) de ligar `coluna` (e zerar as outras dummies do fator)."""
    Xs = X[linhas.to_numpy()]
    x1, x0 = Xs.copy(), Xs.copy()
    x0[outras_do_fator] = 0.0
    x1[outras_do_fator] = 0.0
    x0[coluna] = 0.0
    x1[coluna] = 1.0
    b = res.params.to_numpy()
    p1 = 1 / (1 + np.exp(-(x1.to_numpy() @ b)))
    p0 = 1 / (1 + np.exp(-(x0.to_numpy() @ b)))
    ame = float(np.mean(p1 - p0))
    g = ((p1 * (1 - p1))[:, None] * x1.to_numpy() - (p0 * (1 - p0))[:, None] * x0.to_numpy()).mean(axis=0)
    se = float(np.sqrt(g @ res.cov_params().to_numpy() @ g))
    return ame, se


def ajustar(df: pd.DataFrame, grupos: pd.Series, n_min: int, fatores: list[Fator] | None = None) -> tuple[list[dict], dict]:
    """Ajusta o Logit com erro agrupado e devolve (linhas por (fator, nível) com efeito marginal em p.p., diagnóstico).

    `grupos`: código do IP por linha de df (mesmo índice posicional). `df` precisa de `voltou_7d` e das colunas dos fatores.
    """
    plano = montar_plano(df, n_min, fatores)
    if plano.n_parametros > MAX_PARAMETROS:
        raise ValueError(f"modelo com {plano.n_parametros} parâmetros passa do limite de {MAX_PARAMETROS}: agrupe níveis")
    y = df["voltou_7d"].astype(float)
    X = plano.X
    res = sm.Logit(y, X).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": grupos.to_numpy()})
    erros = np.sqrt(np.diag(res.cov_params()))
    diag = {
        "n_obs": int(len(y)), "eventos": int(y.sum()), "n_parametros": plano.n_parametros, "convergiu": bool(res.mle_retvals["converged"]),
        "n_grupos_ip": int(grupos.nunique()), "condicao_X": float(np.linalg.cond(X.to_numpy())),
        "maior_erro_padrao": float(erros.max()), "maior_coef_abs": float(np.abs(res.params).max()),
        "notas": plano.notas,
    }
    linhas = []
    for (fator, nivel), coluna in plano.colunas_nivel.items():
        irmas = [c for (f2, _), c in plano.colunas_nivel.items() if f2 == fator and c != coluna]
        ame, se = _ame(res, X, coluna, irmas, plano.populacao_ame[fator])
        linhas.append({
            "fator": fator, "nivel": nivel, "efeito_ajustado_pp": ame * 100, "ajustado_ic_inf": (ame - Z * se) * 100,
            "ajustado_ic_sup": (ame + Z * se) * 100, "p_valor": float(2 * norm.sf(abs(ame / se))) if se > 0 else 1.0,
        })
    return linhas, diag


def combinar(brutos: list[dict], ajustados: list[dict]) -> list[dict]:
    """Junta bruto e ajustado, aplica Benjamini-Hochberg, gera `leitura` e `ordem` (|efeito ajustado| decrescente)."""
    aj = {(l["fator"], l["nivel"]): l for l in ajustados}
    linhas = []
    for b in brutos:
        l = {c: b.get(c) for c in COLUNAS_BRUTO}
        a = aj.get((b["fator"], b["nivel"]))
        for c in COLUNAS_AJUSTADO:
            l[c] = None
        if b["grupo"] != ENGAJAMENTO and a is not None:
            for c in ("efeito_ajustado_pp", "ajustado_ic_inf", "ajustado_ic_sup", "p_valor"):
                l[c] = round(a[c], 6 if c == "p_valor" else 4)
            l["leitura"] = None  # depois do Benjamini-Hochberg (precisa saber se sobrevive)
        elif b["grupo"] == ENGAJAMENTO:
            l["leitura"] = leitura_efeito(b["fator"], b["nivel"], b["referencia"], b["efeito_bruto_pp"], b["bruto_ic_inf"], b["bruto_ic_sup"], ajustado=False)
        else:
            l["leitura"] = (f"{ROTULOS.get(b['fator'], b['fator'])}: '{b['nivel']}' tem poucos usuários (n={b['n_nivel']}) e ficou fora do modelo; "
                            f"só a diferença simples, sem levar em conta o perfil, é mostrada.")
        linhas.append(l)
    com_p = [l for l in linhas if l["p_valor"] is not None]
    for l, passa in zip(com_p, benjamini_hochberg([l["p_valor"] for l in com_p])):
        l["significativo_fdr"] = passa
        l["leitura"] = leitura_efeito(l["fator"], l["nivel"], l["referencia"], l["efeito_ajustado_pp"], l["ajustado_ic_inf"],
                                      l["ajustado_ic_sup"], sobrevive_fdr=passa)
    chave = lambda l: (l["efeito_ajustado_pp"] is None, -abs(l["efeito_ajustado_pp"] if l["efeito_ajustado_pp"] is not None else l["efeito_bruto_pp"]))  # noqa: E731
    for pos, l in enumerate(sorted(linhas, key=chave), start=1):
        l["ordem"] = pos
    return linhas


def imprimir_diagnostico(d: dict) -> None:
    print(f"[ajustado] n={d['n_obs']} eventos={d['eventos']} parâmetros={d['n_parametros']} (limite {MAX_PARAMETROS}) "
          f"grupos de IP={d['n_grupos_ip']} convergiu={d['convergiu']}")
    print(f"[ajustado] colinearidade: número de condição de X = {d['condicao_X']:.0f}; separação: maior erro-padrão = "
          f"{d['maior_erro_padrao']:.2f}, maior |coef| = {d['maior_coef_abs']:.2f} (valores muito altos indicam separação)")
    for nota in d["notas"]:
        print(f"[ajustado] nota: {nota}")


def gravar(conn: psycopg.Connection) -> list[dict]:
    """Bruto + ajustado em resultado.efeito_fator (substitui a tabela inteira) e parametros_modelo em resultado.meta."""
    df = carregar_elegiveis(conn)
    n_min = n_minimo(conn)
    grupos_ip = carregar_grupos_ip(conn)
    grupos = grupos_ip.reindex(df["usuario_id"]).reset_index(drop=True)
    df = df.reset_index(drop=True)
    ajustados, diag = ajustar(df, grupos, n_min)
    imprimir_diagnostico(diag)
    linhas = combinar(calcular_bruto(df, n_min), ajustados)
    substituir(conn, "efeito_fator", COLUNAS_EFEITO, [[l[c] for c in COLUNAS_EFEITO] for l in linhas])
    conn.execute("UPDATE resultado.meta SET parametros_modelo = %s", (diag["n_parametros"],))
    return linhas
