"""T-208: o modelo ajustado refeito com outras definições de "usuário" e de "sessão" (REQ-240).

Definições testadas (as mesmas de mart.agg_retencao_sensibilidade): oficial; só IP; IP + user-agent completo; sessão de 60 min.
Cada uma refaz quem é o usuário, qual foi sua 1ª conversa, se voltou em 7 dias e quem é elegível, e reajusta o mesmo Logit
(erro agrupado por IP, mesmos níveis agrupados). Pergunta respondida: o sinal de cada efeito principal se mantém?

As sessões são refeitas em pandas com a MESMA regra de mart.calc_retencao (intervalo medido do fim da conversa anterior ao
início da seguinte, limite inclusivo; retorno até 168 h inclusive; burn-in, maturidade e IPs anômalos iguais). Os testes travam
isso: a definição oficial reproduz mart.fct_primeira_experiencia linha a linha e cada alternativa reproduz o n e os retornos de
mart.agg_retencao_sensibilidade. Só agregados; o IP existe em memória como código.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import psycopg
from scipy.stats import spearmanr

from analise.ajustado import ajustar
from analise.bruto import n_minimo
from analise.fatores import ASSISTENTE, FATORES, PERFIL
from analise.gravar import substituir

# (nome em resultado, coluna da chave de usuário em stg.conversa, gap de sessão em min; None = o oficial de ops.parametros)
DEFINICOES = [
    ("oficial", "usuario_id", None),
    ("so_ip", "usuario_id_ip", None),
    ("ip_ua_completo", "usuario_id_ip_ua", None),
    ("sessao_60min", "usuario_id", 60),   # 60 é o valor ALTERNATIVO testado, não o limiar da definição oficial
]
N_PERFIL = 5

REGIAO = {
    **{e: "Norte" for e in ("Acre", "Amapá", "Amazonas", "Pará", "Rondônia", "Roraima", "Tocantins")},
    **{e: "Nordeste" for e in ("Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe")},
    **{e: "Centro-Oeste" for e in ("Goiás", "Mato Grosso", "Mato Grosso do Sul", "Federal District", "Distrito Federal")},
    **{e: "Sudeste" for e in ("Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo")},
    **{e: "Sul" for e in ("Paraná", "Rio Grande do Sul", "Santa Catarina")},
}

SQL_CONVERSAS = """
SELECT conversa_id, hashed_ip, user_agent, usuario_id, usuario_id_ip, usuario_id_ip_ua, conta_como_uso, ts_inicio, ts_fim,
       modelo_familia, tema, chars_pergunta_1, chars_resposta_1, recusa_1, idioma_pergunta_1, idioma_divergente, fuso, ua_dispositivo, estado
FROM stg.conversa
"""
COLUNAS_COVARIAVEIS = ["modelo_familia", "era_modelo", "tema", "faixa_chars_pergunta", "faixa_chars_resposta", "recusa", "idioma",
                       "idioma_divergente", "periodo_dia", "fim_de_semana", "dispositivo", "regiao"]


# ----------------------------------------------------------------------------------------------- categorização (espelha 30_primeira_experiencia.sql)
def _faixa_pergunta(n: pd.Series) -> pd.Series:
    return pd.Series(np.select([n <= 30, n <= 100, n <= 400], ["até 30", "31–100", "101–400"], "mais de 400"), index=n.index)


def _faixa_resposta(n: pd.Series) -> pd.Series:
    return pd.Series(np.select([n <= 300, n <= 1000, n <= 2500], ["até 300", "301–1.000", "1.001–2.500"], "mais de 2.500"), index=n.index)


def _periodo(h: pd.Series) -> pd.Series:
    return pd.Series(np.select([h <= 5, h <= 11, h <= 17], ["madrugada", "manhã", "tarde"], "noite"), index=h.index)


def covariaveis(primeiras: pd.DataFrame, fuso_pais: str, eras: pd.DataFrame) -> pd.DataFrame:
    """Variáveis da 1ª conversa (linhas de stg.conversa, com `ts_inicio` = início da sessão 1) como em mart.fct_primeira_experiencia."""
    p = primeiras
    local_pais = p["ts_inicio"].dt.tz_convert(fuso_pais).dt.date
    era = pd.Series(None, index=p.index, dtype=object)
    for r in eras.itertuples():
        dentro = (local_pais >= r.inicio) & ((local_pais <= r.fim) if pd.notna(r.fim) else True)
        era = era.where(~dentro, r.era)
    hora = np.zeros(len(p), dtype=int)
    dia = np.zeros(len(p), dtype=int)
    for fuso, idx in p.groupby("fuso").groups.items():  # hora/dia no fuso da própria conversa (por estado), como no SQL
        loc = p.loc[idx, "ts_inicio"].dt.tz_convert(fuso)
        pos = p.index.get_indexer(idx)
        hora[pos] = loc.dt.hour.to_numpy()
        dia[pos] = loc.dt.day_of_week.to_numpy() + 1  # segunda = 1 ... domingo = 7 (isodow)
    estado = p["estado"].where(p["estado"].str.strip().ne(""), None).str.strip()
    return pd.DataFrame({
        "modelo_familia": p["modelo_familia"], "era_modelo": era, "tema": p["tema"].fillna("não classificado"),
        "faixa_chars_pergunta": _faixa_pergunta(p["chars_pergunta_1"]), "faixa_chars_resposta": _faixa_resposta(p["chars_resposta_1"]),
        "recusa": p["recusa_1"].astype(bool), "idioma": p["idioma_pergunta_1"].fillna("Nolang"),
        "idioma_divergente": p["idioma_divergente"].astype(bool),
        "periodo_dia": _periodo(pd.Series(hora, index=p.index)), "fim_de_semana": pd.Series(dia >= 6, index=p.index),
        "dispositivo": p["ua_dispositivo"], "regiao": estado.map(REGIAO).fillna("não informado"),
    })


# ----------------------------------------------------------------------------------------------- usuários sob uma definição
def reconstruir(conv: pd.DataFrame, chave: str, gap_min: int, par: dict, eras: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Elegíveis sob a definição: DataFrame com as covariáveis + `voltou_7d` (+ `chave_usuario` para conferência) e o código do IP da
    sessão 1 (para o erro agrupado). `par`: gap_sessao_min já resolvido não entra aqui; usa janela, burn-in e limiares de ops.parametros."""
    janela = pd.Timedelta(hours=par["janela_retorno_horas"])
    base_ini, base_fim = conv["ts_inicio"].min(), conv["ts_fim"].max()
    ips = conv.groupby("hashed_ip").agg(n=("conversa_id", "size"), uas=("user_agent", "nunique"))
    anomalo = (ips["n"] >= par["limiar_conversas_ip"]) | (ips["uas"] >= par["limiar_uas_ip"])

    c = conv[conv["conta_como_uso"]].copy()
    c["u"] = c[chave]
    c = c.sort_values(["u", "ts_inicio", "conversa_id"], kind="stable")
    fim_anterior = c.groupby("u")["ts_fim"].shift()
    nova = fim_anterior.isna() | ((c["ts_inicio"] - fim_anterior) > pd.Timedelta(minutes=gap_min))
    c["seq"] = nova.groupby(c["u"]).cumsum()
    sessao = c.groupby(["u", "seq"]).agg(ts_ini=("ts_inicio", "min"), hashed_ip=("hashed_ip", "min")).reset_index()
    s1 = sessao[sessao["seq"] == 1].set_index("u")
    outras = sessao[sessao["seq"] > 1].merge(s1[["ts_ini"]].rename(columns={"ts_ini": "ts_primeira"}), left_on="u", right_index=True)
    voltaram = set(outras.loc[outras["ts_ini"] <= outras["ts_primeira"] + janela, "u"])
    primeira = c.groupby("u").head(1).set_index("u").loc[s1.index]   # 1ª conversa que conta como uso = abre a sessão 1

    u = pd.DataFrame({"ts_primeira": s1["ts_ini"], "hashed_ip": s1["hashed_ip"]})
    u["voltou_7d"] = u.index.isin(voltaram)
    u["anomalo"] = u["hashed_ip"].map(anomalo).fillna(False).astype(bool)
    u["elegivel"] = (u["ts_primeira"] + janela <= base_fim) & ~(u["ts_primeira"] < base_ini + pd.Timedelta(days=par["burn_in_dias"])) & ~u["anomalo"]
    primeira = primeira.assign(ts_inicio=u["ts_primeira"])
    cov = covariaveis(primeira, par["fuso_pais"], eras)
    cov["voltou_7d"] = u["voltou_7d"]
    cov["chave_usuario"] = u.index
    cov = cov[u["elegivel"]].reset_index(drop=True)
    codigo_ip, _ = pd.factorize(u.loc[u["elegivel"], "hashed_ip"])
    return cov, codigo_ip


# ----------------------------------------------------------------------------------------------- análise
def escolher_perfil(oficial: list[dict], k: int = N_PERFIL) -> set[tuple[str, str]]:
    """Os k níveis de PERFIL com maior |efeito ajustado| na definição oficial."""
    perfil = {f.nome for f in FATORES if f.grupo == PERFIL}
    cand = sorted((l for l in oficial if l["fator"] in perfil), key=lambda l: -abs(l["efeito_ajustado_pp"]))
    return {(l["fator"], l["nivel"]) for l in cand[:k]}


def comparar(resultados: dict[str, list[dict]]) -> list[dict]:
    """Linhas de resultado.sensibilidade_efeito (assistente + 5 maiores de perfil da oficial) e `mesmo_sinal` contra a oficial."""
    ofi = {(l["fator"], l["nivel"]): l for l in resultados["oficial"]}
    assistente = {f.nome for f in FATORES if f.grupo == ASSISTENTE}
    escolhidos = {k for k in ofi if k[0] in assistente} | escolher_perfil(resultados["oficial"])
    linhas = []
    for nome, _, _ in DEFINICOES:
        atual = {(l["fator"], l["nivel"]): l for l in resultados[nome]}
        for chave in sorted(escolhidos):
            a, o = atual.get(chave), ofi[chave]
            linhas.append({
                "definicao": nome, "fator": chave[0], "nivel": chave[1],
                "efeito_ajustado_pp": None if a is None else round(a["efeito_ajustado_pp"], 4),
                "ic_inf": None if a is None else round(a["ajustado_ic_inf"], 4),
                "ic_sup": None if a is None else round(a["ajustado_ic_sup"], 4),
                "mesmo_sinal": None if a is None else bool(np.sign(a["efeito_ajustado_pp"]) == np.sign(o["efeito_ajustado_pp"])),
            })
    return linhas


def concordancia_de_ordem(resultados: dict[str, list[dict]]) -> dict[str, dict]:
    """Por definição alternativa: quantos níveis em comum, quantos com mesmo sinal e correlação de postos de |efeito| com a oficial."""
    ofi = {(l["fator"], l["nivel"]): abs(l["efeito_ajustado_pp"]) for l in resultados["oficial"]}
    sinal_ofi = {(l["fator"], l["nivel"]): np.sign(l["efeito_ajustado_pp"]) for l in resultados["oficial"]}
    out = {}
    for nome, _, _ in DEFINICOES[1:]:
        alt = {(l["fator"], l["nivel"]): l for l in resultados[nome]}
        comuns = sorted(set(ofi) & set(alt))
        rho = float(spearmanr([ofi[k] for k in comuns], [abs(alt[k]["efeito_ajustado_pp"]) for k in comuns])[0])
        out[nome] = {"niveis_em_comum": len(comuns), "mesmo_sinal": sum(np.sign(alt[k]["efeito_ajustado_pp"]) == sinal_ofi[k] for k in comuns),
                     "correlacao_de_ordem": round(rho, 3)}
    return out


def carregar(conn: psycopg.Connection) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    cur = conn.execute(SQL_CONVERSAS)
    conv = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
    conv["ts_inicio"] = pd.to_datetime(conv["ts_inicio"], utc=True)
    conv["ts_fim"] = pd.to_datetime(conv["ts_fim"], utc=True)
    par = {k: v for k, v in conn.execute("SELECT chave, valor FROM ops.parametros").fetchall()}
    par = {**par, **{k: int(par[k]) for k in ("gap_sessao_min", "janela_retorno_horas", "burn_in_dias", "limiar_conversas_ip", "limiar_uas_ip")}}
    cur = conn.execute("SELECT era, inicio, fim FROM mart.dim_era_modelo ORDER BY inicio")
    eras = pd.DataFrame(cur.fetchall(), columns=["era", "inicio", "fim"])
    return conv, par, eras


def calcular(conv: pd.DataFrame, par: dict, eras: pd.DataFrame, n_min: int) -> tuple[dict[str, list[dict]], dict[str, pd.DataFrame]]:
    resultados, populacoes = {}, {}
    for nome, chave, gap in DEFINICOES:
        df, grupos = reconstruir(conv, chave, gap or par["gap_sessao_min"], par, eras)
        linhas, _ = ajustar(df, pd.Series(grupos), n_min)
        resultados[nome], populacoes[nome] = linhas, df
    return resultados, populacoes


def gravar(conn: psycopg.Connection) -> list[dict]:
    conv, par, eras = carregar(conn)
    resultados, populacoes = calcular(conv, par, eras, n_minimo(conn))
    linhas = comparar(resultados)
    cols = ["definicao", "fator", "nivel", "efeito_ajustado_pp", "ic_inf", "ic_sup", "mesmo_sinal"]
    substituir(conn, "sensibilidade_efeito", cols, [[l[c] for c in cols] for l in linhas])
    for nome, c in concordancia_de_ordem(resultados).items():
        print(f"[sensibilidade] {nome}: n={len(populacoes[nome])}, {c['mesmo_sinal']} de {c['niveis_em_comum']} níveis com o mesmo sinal, "
              f"correlação de ordem (|efeito|) com a oficial = {c['correlacao_de_ordem']}")
    return linhas
