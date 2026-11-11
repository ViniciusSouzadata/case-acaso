"""T-107: agregados (periodo, sensibilidade, segmento), IC de Wilson e dicionario de indicadores.
Nunca imprime texto de conversa. Sintetico: contas feitas a mao (explicadas em cada teste). Real: fechamentos e invariantes."""
import math
import os
from pathlib import Path

import psycopg
import pytest

import esperado
from loader import carregar, migrar, transformar

SNAPSHOT = Path(carregar.SNAPSHOT)

INDICADORES_FIXOS = {
    "taxa_retorno_7d", "novos_usuarios", "voltaram_7d", "ic_95", "media_movel_4s", "usuario", "sessao",
    "primeira_experiencia", "coorte_madura", "amostra_suficiente", "trafego_anomalo",
}
VARIAVEIS = {
    "modelo_familia", "modelo_versao", "era_modelo", "tema", "faixa_chars_pergunta", "faixa_chars_resposta", "recusa",
    "idioma", "idioma_divergente", "n_turnos_sessao", "n_conversas_sessao", "periodo_dia", "dia_semana",
    "fim_de_semana", "dispositivo", "regiao",
}


def _q(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args or None).fetchall()


def _um(sql, *args):
    return _q(sql, *args)[0]


def _wilson_py(k, n, z=1.96):
    """Implementacao independente (Python) da formula de Wilson, para cruzar com o SQL."""
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centro - meia), min(1.0, centro + meia)


def _app_ro_dsn():
    return (f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} dbname={os.environ['POSTGRES_DB']} "
            f"user=app_ro password={os.environ['APP_RO_PASSWORD']}")


# ------------------------------------------------------------------ IC de Wilson (sem depender dos dados)
class TestWilson:
    @pytest.mark.parametrize("k,n,inf,sup", [
        # 12/50: p = 0,24; z² = 3,8416. centro = (0,24 + 0,038416) / 1,076832 = 0,258555;
        # meia = 1,96 * raiz(0,003648 + 0,00038416) / 1,076832 = 1,96 * 0,063499 / 1,076832 = 0,115577
        # -> [0,1430 ; 0,3741]  (a referencia aproximada [0,1430 ; 0,3745] cabe na tolerancia de 1e-3)
        (12, 50, 0.1430, 0.3741),
        # 0/9: limite inferior = 0 (truncado); superior = z² / (n + z²) = 3,8416 / 12,8416 = 0,29915
        (0, 9, 0.0, 0.29915),
        # 30/30: inferior = n / (n + z²) = 30 / 33,8416 = 0,88648; superior = 1
        (30, 30, 0.88648, 1.0),
    ])
    def test_valores_a_mao(self, k, n, inf, sup):
        migrar.migrar()
        i, s = _um("SELECT mart.wilson_inf(%s, %s), mart.wilson_sup(%s, %s)", k, n, k, n)
        assert float(i) == pytest.approx(inf, abs=1e-3)
        assert float(s) == pytest.approx(sup, abs=1e-3)

    def test_n_zero_e_nulo(self):
        migrar.migrar()
        assert _um("SELECT mart.wilson_inf(0, 0), mart.wilson_sup(0, 0), mart.wilson_inf(NULL, 5)") == (None, None, None)

    def test_limites_sempre_dentro_de_0_1_e_contem_p(self):
        migrar.migrar()
        for n in (1, 2, 7, 30, 500):
            for k in range(0, n + 1, max(1, n // 5)):
                i, s = _um("SELECT mart.wilson_inf(%s, %s), mart.wilson_sup(%s, %s)", k, n, k, n)
                assert 0 <= float(i) <= k / n + 1e-6 <= float(s) + 1e-6 <= 1 + 2e-6


# ------------------------------------------------------------------ regra_retorno da calc_retencao
@pytest.mark.usefixtures("usar_sint")  # banco sintético da sessão (conftest.py)
class TestSintetico:
    # ---- outro_dia
    def test_outro_dia_conta_das_regras(self):
        """Elegiveis (20) e quem usou em OUTRO dia local (Sao Paulo, UTC-3) dentro de 168 h da 1a conversa:
        f06, f09, f12 (+2 d); A (02-01 -> 02-08 09:00 UTC = 6d23h, dias locais 01/02 e 08/02); D (+3 d) = 5.
        Nao contam: B (7d+1min, fora da janela); C (10:00 e 10:30 UTC = 07:00 e 07:30 locais, mesmo dia);
        F2 (a 2a conversa e vazia e nao conta como uso); J e K1/K2 (K: duas conversas, mas de usuarios diferentes);
        fillers sem retorno. Total 5/20 -- igual a regra de sessao neste conjunto."""
        assert _um("SELECT usuarios, voltaram_7d FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, NULL, 'outro_dia')") \
            == (20, esperado.RETORNOS_ENTRE_ELEGIVEIS) == (20, 5)

    def test_outro_dia_difere_da_sessao_quando_o_gap_encolhe(self):
        """Com gap de 10 min, a 2a conversa do caso C (20 min apos o FIM da 1a) abre outra sessao: pela regra
        'sessao' C passa a voltar (6/20). Pela regra 'outro_dia' continua 5/20 (mesmo dia local)."""
        assert _um("SELECT voltaram_7d FROM mart.calc_retencao('oficial', 10)")[0] == 6
        assert _um("SELECT voltaram_7d FROM mart.calc_retencao('oficial', 10, NULL, NULL, NULL, NULL, 'outro_dia')")[0] == 5

    def test_outro_dia_usa_o_fuso_da_funcao(self):
        """Fuso extremo (Kiritimati, UTC+14): 10:00 e 10:30 UTC viram 00:00 e 00:30 do dia seguinte: mesmo dia. Mas
        A (02-01 10:00 -> 02-08 09:00 UTC) segue em dias diferentes. Para provar o efeito do fuso: em UTC+14, B (02-02 10:00 ->
        02-09 10:01) sai da janela de qualquer jeito; ja f12 (03-05 13:00 -> 03-07 13:00) segue valendo. Resultado igual (5):
        o que se prova aqui e que o parametro e aceito e usado sem quebrar; o efeito do fuso aparece no real."""
        assert _um("SELECT voltaram_7d FROM mart.calc_retencao('oficial', NULL, 'Pacific/Kiritimati', NULL, NULL, NULL, 'outro_dia')")[0] == 5

    def test_regra_invalida(self):
        with pytest.raises(psycopg.errors.RaiseException):
            _q("SELECT * FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, NULL, 'xyz')")

    def test_chamada_antiga_de_6_argumentos_continua_valendo(self):
        assert _um("SELECT usuarios, voltaram_7d FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, NULL)") == (20, 5)

    # ---- agg_retencao_periodo
    def test_periodo_fechamento_semana_e_mes(self):
        """Fechamento. Universo = usuarios de dim_usuario fora de burn-in e de trafego anomalo = 42 - 12 (E anomalo)
        - 5 (burn-in: H, f01-f04) = 25 (os 20 elegiveis + 5 imaturos: G, f17-f20). Soma de `novos` de TODAS as semanas
        = 25 (imaturas entram com a contagem completa). Soma de `voltaram_7d` das semanas MADURAS = retornos oficiais
        (5), porque a unica semana imatura (25/03) so tem usuarios imaturos."""
        for gran in ("semana", "mes"):
            assert _um("SELECT sum(novos) FROM mart.agg_retencao_periodo WHERE granularidade = %s", gran)[0] == 25
            assert _um("SELECT sum(voltaram_7d) FROM mart.agg_retencao_periodo WHERE granularidade = %s AND madura", gran)[0] \
                <= esperado.RETORNOS_ENTRE_ELEGIVEIS
        assert _um("SELECT sum(novos) FROM mart.agg_retencao_periodo WHERE granularidade = 'semana' AND madura")[0] == 20
        assert _um("SELECT sum(voltaram_7d) FROM mart.agg_retencao_periodo WHERE granularidade = 'semana' AND madura")[0] == 5

    def test_periodo_semanas_a_mao(self):
        """Semanas (segunda no fuso de Sao Paulo): 15/01 f05 (1,0) | 22/01 f06 (1,1) | 29/01 f07,A,B,C,D (5,2) |
        05/02 f08,F2 (2,0) | 12/02 J,K1,K2 (3,0) | 19/02 f09,f10 (2,1) | 26/02 f11 (1,0) | 04/03 f12,f13 (2,1) |
        11/03 f14,f15 (2,0) | 18/03 f16 (1,0) | 25/03 f17-f20,G (5, imatura)."""
        esperado_semanas = {
            "2024-01-15": (1, 0), "2024-01-22": (1, 1), "2024-01-29": (5, 2), "2024-02-05": (2, 0),
            "2024-02-12": (3, 0), "2024-02-19": (2, 1), "2024-02-26": (1, 0), "2024-03-04": (2, 1),
            "2024-03-11": (2, 0), "2024-03-18": (1, 0),
        }
        linhas = {str(r[0]): r[1:] for r in _q(
            "SELECT periodo, novos, voltaram_7d, madura, amostra_suficiente FROM mart.agg_retencao_periodo "
            "WHERE granularidade = 'semana'")}
        assert len(linhas) == 11
        for periodo, (novos, vol) in esperado_semanas.items():
            assert linhas[periodo][:3] == (novos, vol, True), periodo
        assert linhas["2024-03-25"] == (5, None, False, False)  # imatura: novos completo, sem voltaram
        assert not any(l[3] for l in linhas.values())  # nenhuma semana chega a n minimo (30)
        # imatura: taxa e IC nulos
        assert _um("SELECT taxa, ic_inf, ic_sup, taxa_mm4 FROM mart.agg_retencao_periodo "
                   "WHERE granularidade = 'semana' AND periodo = DATE '2024-03-25'") == (None, None, None, None)

    def test_periodo_meses_a_mao(self):
        """Janeiro: f05,f06,f07 (3, voltou 1). Fevereiro: f08-f10, A,B,C,D, F2, J, K1, K2 (11, voltaram f09,A,D = 3).
        Marco: f11-f16 elegiveis (6, voltou f12) + 5 imaturos = 11 novos, mes imaturo (sem taxa)."""
        linhas = {str(r[0]): r[1:] for r in _q(
            "SELECT periodo, novos, voltaram_7d, madura FROM mart.agg_retencao_periodo WHERE granularidade = 'mes'")}
        assert linhas == {"2024-01-01": (3, 1, True), "2024-02-01": (11, 3, True), "2024-03-01": (11, None, False)}

    def test_media_movel_4_semanas_a_mao(self):
        """Primeiras 3 semanas: menos de 4 semanas -> NULL. 05/02: semanas 15/01,22/01,29/01,05/02 = voltaram 0+1+2+0 = 3,
        novos 1+1+5+2 = 9 -> 0,333333. 12/02: 22/01..12/02 = voltaram 1+2+0+0 = 3, novos 1+5+2+3 = 11 -> 0,272727."""
        mm = {str(r[0]): r[1] for r in _q(
            "SELECT periodo, taxa_mm4 FROM mart.agg_retencao_periodo WHERE granularidade = 'semana'")}
        for p in ("2024-01-15", "2024-01-22", "2024-01-29", "2024-03-25"):
            assert mm[p] is None, p
        assert float(mm["2024-02-05"]) == pytest.approx(3 / 9, abs=1e-6)
        assert float(mm["2024-02-12"]) == pytest.approx(3 / 11, abs=1e-6)
        assert _um("SELECT count(*) FROM mart.agg_retencao_periodo WHERE granularidade = 'mes' AND taxa_mm4 IS NOT NULL")[0] == 0

    def test_periodo_ic_confere_com_python(self):
        for novos, vol, inf, sup in _q(
                "SELECT novos, voltaram_7d, ic_inf, ic_sup FROM mart.agg_retencao_periodo WHERE madura"):
            i, s = _wilson_py(vol, novos)
            assert float(inf) == pytest.approx(i, abs=1e-5) and float(sup) == pytest.approx(s, abs=1e-5)

    # ---- sensibilidade
    def test_sensibilidade_linhas_e_oficial(self):
        linhas = {r[0]: r[1:] for r in _q(
            "SELECT definicao, usuarios, voltaram_7d, taxa, delta_vs_oficial FROM mart.agg_retencao_sensibilidade")}
        assert set(linhas) == {"oficial", "so_ip", "ip_ua_completo", "sessao_60min", "outro_dia", "sem_burn_in",
                               "com_trafego_anomalo", "com_perguntas_vazias", "fuso_utc"}
        assert linhas["oficial"][:2] == (20, 5)
        assert float(linhas["oficial"][2]) == pytest.approx(5 / 20)
        assert float(linhas["oficial"][3]) == 0
        # contas a mao (ver esperado.py): so IP: K junta 2 usuarios em 1 e E segue anomalo -> 19 elegiveis, 6 voltam
        #   (K, unico por IP, tem 2 sessoes a 2 d); sem burn-in: +H +f01..f04 = 25, 5 voltam (-5,00 p.p.);
        #   com anomalo: +12 usuarios de E = 32, 5 voltam (-9,38 p.p.); com perguntas vazias: +F (sem retorno) = 21 e
        #   F2 passa a voltar (3 d depois, conversa vazia agora conta) = 6; sessao 60 min: nada muda (C ja era 1 sessao).
        assert linhas["so_ip"][:2] == (19, 6)
        assert linhas["sem_burn_in"][:2] == (25, 5)
        assert float(linhas["sem_burn_in"][3]) == pytest.approx(-5.00, abs=0.01)
        assert linhas["com_trafego_anomalo"][:2] == (32, 5)
        assert float(linhas["com_trafego_anomalo"][3]) == pytest.approx(-9.38, abs=0.01)
        assert linhas["com_perguntas_vazias"][:2] == (21, 6)
        assert linhas["sessao_60min"][:2] == (20, 5)
        assert linhas["outro_dia"][:2] == (20, 5)
        assert linhas["fuso_utc"][:2] == (20, 5)

    def test_sensibilidade_fuso_utc_descricao_a_mao(self):
        """Mudaria de semana quem chegou entre domingo 21h e 24h locais (= segunda 00h-03h UTC). Nenhum dos 20 elegiveis
        sinteticos cai nessa janela (o mais proximo, f10, chegou domingo 20:00 UTC = 17:00 local, mesma semana)."""
        desc = _um("SELECT descricao FROM mart.agg_retencao_sensibilidade WHERE definicao = 'fuso_utc'")[0]
        assert " 0 usuários elegíveis" in desc

    def test_sensibilidade_ic_confere_com_python(self):
        for usuarios, vol, inf, sup in _q("SELECT usuarios, voltaram_7d, ic_inf, ic_sup FROM mart.agg_retencao_sensibilidade"):
            i, s = _wilson_py(vol, usuarios)
            assert float(inf) == pytest.approx(i, abs=1e-5) and float(sup) == pytest.approx(s, abs=1e-5)

    # ---- segmento
    def test_segmento_toda_variavel_soma_os_elegiveis(self):
        assert {r[0] for r in _q("SELECT DISTINCT variavel FROM mart.agg_retencao_segmento")} == VARIAVEIS
        for variavel, total, vol in _q("SELECT variavel, sum(novos), sum(voltaram_7d) FROM mart.agg_retencao_segmento GROUP BY 1"):
            assert (total, vol) == (20, 5), variavel

    def test_segmento_a_mao(self):
        """Toda a base sintetica usa gpt-3.5, 'Portuguese', e UA de Windows/Mac/Android/iOS: modelo_familia e idioma tem 1 valor."""
        assert len(_q("SELECT 1 FROM mart.agg_retencao_segmento WHERE variavel = 'modelo_familia'")) == 1
        assert _q("SELECT valor FROM mart.agg_retencao_segmento WHERE variavel = 'idioma'") == [("Portuguese",)]
        # n_conversas_sessao: so C tem 2 conversas na sessao 1
        assert _q("SELECT valor, novos FROM mart.agg_retencao_segmento WHERE variavel = 'n_conversas_sessao' ORDER BY valor") \
            == [("1", 19), ("2+", 1)]
        assert _um("SELECT bool_or(amostra_suficiente) FROM mart.agg_retencao_segmento")[0] is False

    # ---- dicionario
    def test_dicionario_cobre_indicadores_e_variaveis(self):
        usados = INDICADORES_FIXOS | {r[0] for r in _q("SELECT DISTINCT variavel FROM mart.agg_retencao_segmento")}
        no_dic = {r[0] for r in _q("SELECT indicador FROM mart.dicionario_indicador")}
        assert usados <= no_dic, usados - no_dic
        assert len(no_dic) == len(INDICADORES_FIXOS) + len(VARIAVEIS)

    def test_dicionario_nenhum_campo_vazio_e_versao(self):
        colunas = ["indicador", "nome_exibicao", "definicao", "formula", "denominador", "periodo_referencia", "fonte",
                   "sql_referencia", "limitacoes", "versao_definicao"]
        for col in colunas:
            assert _um(f"SELECT count(*) FROM mart.dicionario_indicador WHERE {col} IS NULL OR btrim({col}) = ''")[0] == 0, col
        versao = _um("SELECT ops.param('versao_definicao')")[0]
        assert _q("SELECT DISTINCT versao_definicao FROM mart.dicionario_indicador") == [(versao,)]

    def test_dicionario_numeros_de_definicao_vem_dos_parametros(self):
        """O texto acompanha ops.parametros: mudar o gap muda a frase da sessao no dicionario."""
        try:
            with psycopg.connect(migrar.dsn(), autocommit=True) as c:
                c.execute("UPDATE ops.parametros SET valor = '45' WHERE chave = 'gap_sessao_min'")
            transformar.transformar()
            assert "45 minutos" in _um("SELECT definicao FROM mart.dicionario_indicador WHERE indicador = 'sessao'")[0]
        finally:
            with psycopg.connect(migrar.dsn(), autocommit=True) as c:
                c.execute("UPDATE ops.parametros SET valor = '30' WHERE chave = 'gap_sessao_min'")
            transformar.transformar()
        assert "30 minutos" in _um("SELECT definicao FROM mart.dicionario_indicador WHERE indicador = 'sessao'")[0]

    def test_dicionario_sem_texto_de_conversa_nem_ip(self):
        # os agregados nao tem coluna de identidade: confere nomes de colunas dos 4 marts novos
        cols = {r[0] for r in _q(
            "SELECT column_name FROM information_schema.columns WHERE table_schema = 'mart' AND table_name IN "
            "('agg_retencao_periodo','agg_retencao_sensibilidade','agg_retencao_segmento','dicionario_indicador')")}
        assert not (cols & {"hashed_ip", "user_agent", "usuario_id", "content", "pergunta", "resposta"})

    def test_app_ro_le_as_tabelas_novas(self):
        with psycopg.connect(_app_ro_dsn()) as c:
            for tabela in ("agg_retencao_periodo", "agg_retencao_sensibilidade", "agg_retencao_segmento", "dicionario_indicador"):
                assert c.execute(f"SELECT count(*) FROM mart.{tabela}").fetchone()[0] > 0, tabela

    def test_sem_tabela_novo_sobrando_e_pkeys(self):
        assert _q("SELECT tablename FROM pg_tables WHERE schemaname = 'mart' AND tablename LIKE '%\\_novo'") == []
        indices = {r[0] for r in _q("SELECT indexname FROM pg_indexes WHERE schemaname = 'mart'")}
        assert {"agg_retencao_periodo_pkey", "agg_retencao_sensibilidade_pkey", "agg_retencao_segmento_pkey",
                "dicionario_indicador_pkey"} <= indices


# ------------------------------------------------------------------ snapshot real
@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="snapshot real ausente")
@pytest.mark.usefixtures("usar_real")  # banco real da sessão (conftest.py)
class TestReal:
    def test_sensibilidade_oficial_e_a_taxa_global(self):
        usuarios, vol, taxa = _um("SELECT usuarios, voltaram_7d, taxa FROM mart.agg_retencao_sensibilidade WHERE definicao = 'oficial'")
        assert (usuarios, vol) == (2372, 566)
        assert float(taxa) == pytest.approx(566 / 2372, abs=1e-6)
        el, vo = _um("SELECT count(*), count(*) FILTER (WHERE voltou_7d) FROM mart.fct_primeira_experiencia WHERE elegivel")
        assert (el, vo) == (2372, 566)

    def test_sensibilidade_valores_do_state(self):
        d = {r[0]: r[1:] for r in _q("SELECT definicao, usuarios, voltaram_7d FROM mart.agg_retencao_sensibilidade")}
        assert d["so_ip"] == (2239, 536) and d["ip_ua_completo"] == (2657, 668) and d["sessao_60min"] == (2372, 511)
        assert len(d) == 9

    def test_fuso_utc_descricao_confere_com_conta_independente(self):
        n = _um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel AND "
                "date_trunc('week', ts_primeira AT TIME ZONE 'UTC')::date <> date_trunc('week', ts_primeira AT TIME ZONE 'America/Sao_Paulo')::date")[0]
        desc = _um("SELECT descricao FROM mart.agg_retencao_sensibilidade WHERE definicao = 'fuso_utc'")[0]
        assert f" {n} usuários elegíveis" in desc

    @pytest.mark.parametrize("gran", ["semana", "mes"])
    def test_periodo_fechamento(self, gran):
        """soma de novos (todos os periodos, maduros ou nao) = usuarios fora de burn-in e de trafego anomalo; a soma de
        voltaram_7d dos periodos maduros e <= retornos oficiais (os imaturos nao mostram voltaram)."""
        fora = _um("SELECT count(*) FROM mart.dim_usuario WHERE NOT burn_in AND NOT trafego_anomalo")[0]
        assert _um("SELECT sum(novos) FROM mart.agg_retencao_periodo WHERE granularidade = %s", gran)[0] == fora
        vol_madura = _um("SELECT sum(voltaram_7d) FROM mart.agg_retencao_periodo WHERE granularidade = %s AND madura", gran)[0]
        assert vol_madura <= 566
        # maduros + imaturos = elegiveis + imaturos
        assert _um("SELECT sum(novos) FROM mart.agg_retencao_periodo WHERE granularidade = %s AND madura", gran)[0] <= 2372
        assert _um("SELECT count(*) FROM mart.agg_retencao_periodo WHERE granularidade = %s AND NOT madura "
                   "AND (voltaram_7d IS NOT NULL OR taxa IS NOT NULL OR ic_inf IS NOT NULL OR ic_sup IS NOT NULL)", gran)[0] == 0
        assert _um("SELECT count(*) FROM mart.agg_retencao_periodo WHERE madura AND voltaram_7d > novos")[0] == 0

    def test_periodo_ic_e_media_movel_conferem_com_python(self):
        for novos, vol, inf, sup in _q("SELECT novos, voltaram_7d, ic_inf, ic_sup FROM mart.agg_retencao_periodo WHERE madura"):
            i, s = _wilson_py(vol, novos)
            assert float(inf) == pytest.approx(i, abs=1e-5) and float(sup) == pytest.approx(s, abs=1e-5)
        semanas = _q("SELECT periodo, novos, voltaram_7d, madura, taxa_mm4 FROM mart.agg_retencao_periodo "
                     "WHERE granularidade = 'semana' ORDER BY periodo")
        por = {r[0]: r for r in semanas}
        for periodo, novos, vol, madura, mm in semanas:
            janela = [por.get(periodo.fromordinal(periodo.toordinal() - 7 * j)) for j in range(4)]
            ok = madura and all(j is not None and j[3] for j in janela)
            if not ok:
                assert mm is None, periodo
            else:
                assert float(mm) == pytest.approx(sum(j[2] for j in janela) / sum(j[1] for j in janela), abs=1e-6)

    def test_semanas_madura_imatura_e_amostra(self):
        sem = _q("SELECT madura, amostra_suficiente, count(*) FROM mart.agg_retencao_periodo WHERE granularidade = 'semana' GROUP BY 1, 2")
        assert sum(r[2] for r in sem) > 40  # abr/2023..abr/2024: ~50 semanas
        assert any(r[0] is False for r in sem)  # a ultima semana e imatura

    def test_segmento_toda_variavel_soma_os_elegiveis(self):
        assert {r[0] for r in _q("SELECT DISTINCT variavel FROM mart.agg_retencao_segmento")} == VARIAVEIS
        for variavel, total, vol in _q("SELECT variavel, sum(novos), sum(voltaram_7d) FROM mart.agg_retencao_segmento GROUP BY 1"):
            assert (total, vol) == (2372, 566), variavel
        assert _um("SELECT count(*) FROM mart.agg_retencao_segmento WHERE variavel = 'idioma'")[0] <= 4
        for inf, taxa, sup in _q("SELECT ic_inf, taxa, ic_sup FROM mart.agg_retencao_segmento"):
            assert float(inf) <= float(taxa) <= float(sup)

    def test_dicionario_completo(self):
        usados = INDICADORES_FIXOS | {r[0] for r in _q("SELECT DISTINCT variavel FROM mart.agg_retencao_segmento")}
        assert usados <= {r[0] for r in _q("SELECT indicador FROM mart.dicionario_indicador")}

    def test_app_ro_le_as_tabelas_novas(self):
        with psycopg.connect(_app_ro_dsn()) as c:
            assert c.execute("SELECT count(*) FROM mart.agg_retencao_periodo").fetchone()[0] > 0
            assert c.execute("SELECT count(*) FROM mart.dicionario_indicador").fetchone()[0] == 27
