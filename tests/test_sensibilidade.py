"""T-208: sessões e usuários refeitos em pandas batem com o banco; sensibilidade grava assistente + 5 maiores de perfil."""
import pandas as pd
import psycopg
import pytest

from analise import sensibilidade as S
from loader.migrar import dsn

PAR = {"janela_retorno_horas": 168, "burn_in_dias": 14, "limiar_conversas_ip": 200, "limiar_uas_ip": 10, "fuso_pais": "America/Sao_Paulo",
       "gap_sessao_min": 30}
ERAS = pd.DataFrame({"era": ["e1"], "inicio": [pd.Timestamp("2023-04-01").date()], "fim": [pd.NaT]})


def _conv(cid, usuario, ip, inicio, fim, uso=True, ua="ua"):
    return {"conversa_id": cid, "hashed_ip": ip, "user_agent": ua, "usuario_id": usuario, "usuario_id_ip": ip, "usuario_id_ip_ua": usuario + ua,
            "conta_como_uso": uso, "ts_inicio": pd.Timestamp(inicio, tz="UTC"), "ts_fim": pd.Timestamp(fim, tz="UTC"),
            "modelo_familia": "gpt-3.5", "tema": "outros/indefinido", "chars_pergunta_1": 50, "chars_resposta_1": 500, "recusa_1": False,
            "idioma_pergunta_1": "Portuguese", "idioma_divergente": False, "fuso": "America/Sao_Paulo", "ua_dispositivo": "computador",
            "estado": "São Paulo"}


def _base(extra):
    """Conversas de borda (início e fim da base) + as do caso testado. O usuário 'x' começa em 10/05/2023: fora do burn-in e maduro."""
    return pd.DataFrame([_conv(1, "borda1", "ipA", "2023-04-01 00:00", "2023-04-01 00:10"),
                         _conv(2, "borda2", "ipB", "2023-07-01 00:00", "2023-07-01 00:10"), *extra])


def test_sessao_30_x_60_min_muda_quem_voltou_feito_a_mao():
    # conversa 1 termina 10:00; a 2ª começa 10:45 (intervalo de 45 min): com gap 30 é sessão nova (voltou); com gap 60 é a mesma (não voltou)
    conv = _base([_conv(10, "x", "ipX", "2023-05-10 09:50", "2023-05-10 10:00"), _conv(11, "x", "ipX", "2023-05-10 10:45", "2023-05-10 10:50")])
    a30, _ = S.reconstruir(conv, "usuario_id", 30, PAR, ERAS)
    a60, _ = S.reconstruir(conv, "usuario_id", 60, PAR, ERAS)
    assert a30.set_index("chave_usuario").loc["x", "voltou_7d"] and not a60.set_index("chave_usuario").loc["x", "voltou_7d"]


def test_intervalo_exato_e_janela_de_168h_sao_inclusivos():
    # intervalo exatamente 30 min: mesma sessão (<= gap); retorno exatamente 168 h depois do início da 1ª sessão: conta
    conv = _base([_conv(10, "y", "ipY", "2023-05-10 09:50", "2023-05-10 10:00"), _conv(11, "y", "ipY", "2023-05-10 10:30", "2023-05-10 10:35"),
                  _conv(12, "z", "ipZ", "2023-05-10 09:50", "2023-05-10 10:00"), _conv(13, "z", "ipZ", "2023-05-17 09:50", "2023-05-17 09:55"),
                  _conv(14, "w", "ipW", "2023-05-10 09:50", "2023-05-10 10:00"), _conv(15, "w", "ipW", "2023-05-17 09:51", "2023-05-17 09:55")])
    r, _ = S.reconstruir(conv, "usuario_id", 30, PAR, ERAS)
    v = r.set_index("chave_usuario")["voltou_7d"]
    assert not v["y"] and v["z"] and not v["w"]   # y: mesma sessão; z: 168 h exatas; w: 168 h + 1 min


def test_imaturo_burn_in_e_ip_anomalo_ficam_de_fora():
    cedo = _conv(20, "cedo", "ipC", "2023-04-03 10:00", "2023-04-03 10:05")          # dentro dos 14 dias de burn-in
    tarde = _conv(21, "tarde", "ipT", "2023-06-28 10:00", "2023-06-28 10:05")        # < 168 h do fim da base: imaturo
    anomalos = [_conv(100 + i, f"mass{i}", "ipM", "2023-05-10 12:00", "2023-05-10 12:01", ua=f"ua{i}") for i in range(11)]  # 11 UAs: anômalo
    ok = _conv(22, "ok", "ipO", "2023-05-10 09:50", "2023-05-10 10:00")
    r, _ = S.reconstruir(_base([cedo, tarde, ok, *anomalos]), "usuario_id", 30, PAR, ERAS)
    assert set(r["chave_usuario"]) == {"ok"}


def test_categorizacao_das_covariaveis():
    conv = _base([{**_conv(30, "k", "ipK", "2023-05-10 09:50", "2023-05-10 10:00"), "chars_pergunta_1": 31, "chars_resposta_1": 2501, "estado": "Piauí",
                   "fuso": "America/Manaus", "recusa_1": True}])
    r, _ = S.reconstruir(conv, "usuario_id", 30, PAR, ERAS)
    k = r.set_index("chave_usuario").loc["k"]
    assert (k["faixa_chars_pergunta"], k["faixa_chars_resposta"], k["regiao"], k["recusa"], k["era_modelo"]) == ("31–100", "mais de 2.500", "Nordeste", True, "e1")
    assert k["periodo_dia"] == "madrugada"    # 09:50 UTC em Manaus (UTC-4) = 05:50


def test_comparar_mesmo_sinal_e_perfil_top5():
    def lin(f, n, e):
        return {"fator": f, "nivel": n, "efeito_ajustado_pp": e, "ajustado_ic_inf": e - 1, "ajustado_ic_sup": e + 1}
    base = [lin("recusa", "sim", -3.0), lin("modelo_familia", "gpt-4", 2.0)] + [lin("dispositivo", "celular", 1.0)] + \
           [lin("regiao", f"r{i}", 10.0 - i) for i in range(6)] + [lin("periodo_dia", "manhã", 0.1)]
    alt = [lin("recusa", "sim", 1.0), lin("modelo_familia", "gpt-4", 3.0)] + [lin("dispositivo", "celular", 1.0)] + \
          [lin("regiao", f"r{i}", 10.0 - i) for i in range(6)] + [lin("periodo_dia", "manhã", 0.1)]
    res = {"oficial": base, "so_ip": alt, "ip_ua_completo": base, "sessao_60min": alt[:2]}
    linhas = S.comparar(res)
    top = {(l["fator"], l["nivel"]) for l in linhas if l["fator"] in ("regiao", "dispositivo", "periodo_dia")}
    assert top == {("regiao", f"r{i}") for i in range(5)}                                # as 5 maiores de perfil, só elas
    d = {(l["definicao"], l["fator"]): l for l in linhas}
    assert d[("so_ip", "recusa")]["mesmo_sinal"] is False and d[("so_ip", "modelo_familia")]["mesmo_sinal"] is True
    assert d[("oficial", "recusa")]["mesmo_sinal"] is True
    assert d[("sessao_60min", "regiao")]["efeito_ajustado_pp"] is None and d[("sessao_60min", "regiao")]["mesmo_sinal"] is None  # nível ausente


def test_concordancia_de_ordem():
    def res(vals):
        return [{"fator": "f", "nivel": str(i), "efeito_ajustado_pp": v} for i, v in enumerate(vals)]
    r = {"oficial": res([5, -4, 3, 2, 1]), "so_ip": res([5, -4, 3, 2, 1]), "ip_ua_completo": res([1, 2, 3, 4, 5]), "sessao_60min": res([5, 4, -3, 2, 1])}
    c = S.concordancia_de_ordem(r)
    assert c["so_ip"]["correlacao_de_ordem"] == 1.0 and c["so_ip"]["mesmo_sinal"] == 5
    assert c["ip_ua_completo"]["correlacao_de_ordem"] == -1.0
    assert c["sessao_60min"]["mesmo_sinal"] == 3 + 0 or c["sessao_60min"]["mesmo_sinal"] == 4  # sinais: 5+,4≠-4,−3≠+3,2,1


@pytest.mark.usefixtures("usar_real")
def test_reconstrucao_oficial_bate_com_o_mart_e_alternativas_com_a_sensibilidade():
    with psycopg.connect(dsn(), autocommit=True) as c:
        conv, par, eras = S.carregar(c)
        fct = pd.DataFrame(c.execute(
            "SELECT usuario_id, modelo_familia, era_modelo, tema, faixa_chars_pergunta, faixa_chars_resposta, recusa, idioma, idioma_divergente, "
            "periodo_dia, fim_de_semana, dispositivo, regiao, voltou_7d FROM mart.fct_primeira_experiencia WHERE elegivel").fetchall(),
            columns=["usuario_id", *S.COLUNAS_COVARIAVEIS, "voltou_7d"])
        agg = {d: (int(u), int(v)) for d, u, v in c.execute(
            "SELECT definicao, usuarios, voltaram_7d FROM mart.agg_retencao_sensibilidade")}
    ofi, _ = S.reconstruir(conv, "usuario_id", par["gap_sessao_min"], par, eras)
    a = ofi.set_index("chave_usuario").sort_index()
    b = fct.set_index("usuario_id").sort_index()
    assert list(a.index) == list(b.index)                                             # mesmos usuários elegíveis
    for col in [*S.COLUNAS_COVARIAVEIS, "voltou_7d"]:
        assert (a[col].astype(object).to_numpy() == b[col].astype(object).to_numpy()).all(), col
    for nome, chave, gap in S.DEFINICOES[1:]:
        df, _ = S.reconstruir(conv, chave, gap or par["gap_sessao_min"], par, eras)
        assert (len(df), int(df["voltou_7d"].sum())) == agg[nome], nome


@pytest.mark.usefixtures("usar_real")
def test_sensibilidade_real_grava_assistente_e_cinco_de_perfil():
    with psycopg.connect(dsn(), autocommit=True) as c:
        from analise import ajustado, meta
        meta.gravar(c)
        ajustado.gravar(c)
        linhas = S.gravar(c)
        tab = pd.DataFrame(c.execute("SELECT definicao, fator, nivel, efeito_ajustado_pp, ic_inf, ic_sup, mesmo_sinal FROM resultado.sensibilidade_efeito").fetchall(),
                           columns=["definicao", "fator", "nivel", "ef", "inf", "sup", "sinal"])
        oficial = {(f, n): float(e) for f, n, e in c.execute(
            "SELECT fator, nivel, efeito_ajustado_pp FROM resultado.efeito_fator WHERE metodo = 'logit_ame' AND efeito_ajustado_pp IS NOT NULL")}
    assert len(linhas) == len(tab) and set(tab["definicao"]) == {"oficial", "so_ip", "ip_ua_completo", "sessao_60min"}
    por_def = tab.groupby("definicao").size()
    assert por_def.nunique() == 1 and por_def.iloc[0] == 6 + 5                         # 6 níveis de assistente + 5 de perfil
    assert {"recusa", "idioma_divergente", "faixa_chars_resposta", "modelo_familia"} <= set(tab["fator"])
    o = tab[tab["definicao"] == "oficial"]
    assert o["sinal"].all()
    for r in o.itertuples():   # a oficial refeita em pandas = a oficial gravada pelo modelo principal
        assert float(r.ef) == pytest.approx(oficial[(r.fator, r.nivel)], abs=1e-3)
    com_ef = tab.dropna(subset=["ef"])
    assert (com_ef["inf"].astype(float) < com_ef["ef"].astype(float)).all() and (com_ef["ef"].astype(float) < com_ef["sup"].astype(float)).all()


def test_uniao_das_definicoes_inclui_as_primeiras_conversas_de_cada_chave():
    from analise import uniao_definicoes as U
    # mesmo IP, dois navegadores: na chave oficial são 2 usuários (2 primeiras conversas); só por IP, 1 usuário (a mais antiga)
    a = {**_conv(10, "x1", "ipX", "2023-05-10 09:50", "2023-05-10 10:00", ua="uaA"), "usuario_id_ip": "ipX", "usuario_id_ip_ua": "ipXuaA"}
    b = {**_conv(11, "x2", "ipX", "2023-05-10 12:00", "2023-05-10 12:05", ua="uaB"), "usuario_id_ip": "ipX", "usuario_id_ip_ua": "ipXuaB"}
    por_def = U.ids_por_definicao(_base([a, b]), PAR, ERAS)
    assert por_def["oficial"] == {10, 11} and por_def["so_ip"] == {10} and por_def["ip_ua_completo"] == {10, 11}
    assert U.uniao(por_def) == {10, 11}
    c = U.contagens(por_def)
    assert c["oficial"] == 2 and c["so_ip"] == 1 and c["uniao"] == 2 and c["so_na_uniao"] == 0
