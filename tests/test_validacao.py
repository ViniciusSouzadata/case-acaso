"""T-205b: kappa contra valor de referência, métricas, amostra estratificada, anonimização e gravação da validação."""
import csv
from pathlib import Path

import psycopg
import pytest

from analise import validacao
from classificador.tema import TAXONOMIA
from loader.migrar import dsn


def _mistura(n_ss, n_sn, n_ns, n_nn):
    """Humano/máquina com os rótulos 'sim'/'não' nas contagens dadas."""
    h = ["sim"] * n_ss + ["sim"] * n_sn + ["não"] * n_ns + ["não"] * n_nn
    m = ["sim"] * n_ss + ["não"] * n_sn + ["sim"] * n_ns + ["não"] * n_nn
    return h, m


def test_kappa_exemplo_de_referencia_feito_a_mao():
    # 50 avaliações: 20 sim/sim, 5 sim/não, 10 não/sim, 15 não/não. po = 35/50 = 0,7;
    # pe = (25/50)(30/50) + (25/50)(20/50) = 0,30 + 0,20 = 0,50; kappa = (0,7 - 0,5) / (1 - 0,5) = 0,4
    h, m = _mistura(20, 5, 10, 15)
    assert validacao.acuracia(h, m) == pytest.approx(0.7)
    assert validacao.kappa_cohen(h, m) == pytest.approx(0.4)


def test_kappa_concordancia_total_e_so_acaso():
    h = ["a", "b", "a", "b"]
    assert validacao.kappa_cohen(h, h) == pytest.approx(1.0)
    assert validacao.kappa_cohen(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)  # po = 0,5 = pe
    assert validacao.kappa_cohen(["a"] * 4, ["a"] * 4) == 1.0  # um só rótulo dos dois lados


def test_matriz_e_por_classe():
    h, m = _mistura(20, 5, 10, 15)
    mc = validacao.matriz_confusao(h, m)
    assert mc == {"não": {"sim": 10, "não": 15}, "sim": {"sim": 20, "não": 5}}
    pc = validacao.por_classe(h, m)
    assert pc["sim"]["precisao"] == pytest.approx(20 / 30, abs=1e-4) and pc["sim"]["revocacao"] == pytest.approx(20 / 25, abs=1e-4)  # arredondado em 4 casas
    r = validacao.resumo_metricas(h, m)
    assert r["n"] == 50 and r["kappa"] == pytest.approx(0.4)


def _candidatos():
    c = []
    for i in range(400):
        c.append((1000 + i, TAXONOMIA[i % 8], i % 10 == 0))  # 10% com recusa prevista
    return c


def test_amostra_estratificada_tamanho_recusa_e_equilibrio_entre_temas():
    esc = validacao.sortear_estratificada(_candidatos(), 80, 20)
    assert len(esc) == len(set(esc)) == 80
    prev = {c: (t, r) for c, t, r in _candidatos()}
    assert sum(1 for c in esc if prev[c][1]) == 20
    por_tema = {t: sum(1 for c in esc if prev[c][0] == t and not prev[c][1]) for t in TAXONOMIA}
    assert max(por_tema.values()) - min(por_tema.values()) <= 1  # revezamento entre temas
    assert esc == validacao.sortear_estratificada(_candidatos(), 80, 20)  # semente fixa: mesma amostra


def test_amostra_cobre_quando_um_estrato_esvazia():
    c = [(i, "a", False) for i in range(30)] + [(100 + i, "b", False) for i in range(3)]
    esc = validacao.sortear_estratificada(c, 20, 0)
    assert len(esc) == 20 and sum(1 for x in esc if x >= 100) == 3  # "b" inteiro entra; "a" completa


def test_normalizar_recusa():
    assert validacao.normalizar_recusa(" Sim ") == "sim" and validacao.normalizar_recusa("NAO") == "não"
    with pytest.raises(ValueError):
        validacao.normalizar_recusa("talvez")


def _preenchida(caminho: Path, linhas):
    with caminho.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(validacao.CABECALHO_PLANILHA)
        for i, (cid, tema, rec) in enumerate(linhas, start=1):
            w.writerow([i, cid, "texto que NÃO pode ir para o git", "resposta idem", tema, rec])


def test_anonimizar_guarda_so_id_e_rotulos(tmp_path):
    pre, saida = tmp_path / "pre.csv", tmp_path / "rot.csv"
    _preenchida(pre, [(11, "programação/TI", "Sim"), (12, "outros/indefinido", "não")])
    assert validacao.anonimizar(pre, saida) == 2
    texto = saida.read_text(encoding="utf-8")
    assert texto.splitlines()[0] == "conversa_id,tema_vinicius,recusa_vinicius" and "texto" not in texto and "resposta" not in texto
    assert validacao.ler_rotulos(saida) == {11: ("programação/TI", "sim"), 12: ("outros/indefinido", "não")}


def test_anonimizar_recusa_tema_fora_da_taxonomia(tmp_path):
    pre = tmp_path / "pre.csv"
    _preenchida(pre, [(11, "culinária", "sim")])
    with pytest.raises(ValueError, match="tema_vinicius inválido"):
        validacao.anonimizar(pre, tmp_path / "rot.csv")


@pytest.mark.usefixtures("usar_real")
def test_validar_grava_uma_linha_por_classificador_nas_200_completas(tmp_path):
    """Cada classificador é avaliado nas mesmas conversas; o seed de tema do banco não entra na conta."""
    ids = list(range(1000, 1060))
    rot, prev = tmp_path / "rot.csv", tmp_path / "prev.csv"
    with rot.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(validacao.CABECALHO_ROTULOS)
        for i, cid in enumerate(ids):
            w.writerow([cid, "programação/TI", "sim" if i < 10 else "não"])
    with prev.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["conversa_id", "classificador", "versao", "tema", "recusa"])
        for i, cid in enumerate(ids):   # regras: erra o tema nas 6 primeiras e a recusa nas 3 primeiras
            w.writerow([cid, "regras", "9.9.9|8.8.8", "outros/indefinido" if i < 6 else "programação/TI", "false" if i < 3 else ("true" if i < 10 else "false")])
        for i, cid in enumerate(ids):   # LLM: acerta tudo
            w.writerow([cid, "openrouter:x/y", "or-1", "programação/TI", "true" if i < 10 else "false"])
    with psycopg.connect(dsn(), autocommit=True) as c:
        r = validacao.validar(c, rot, prev)
        gravado = c.execute("SELECT classificador, modelo, n, acuracia FROM resultado.validacao_classificador ORDER BY modelo, classificador").fetchall()
    assert [(x["classificador"], x["modelo"]) for x in r] == [("tema", "regras:9.9.9"), ("recusa", "regras"),
                                                              ("tema", "openrouter:x/y"), ("recusa", "openrouter:x/y")]
    assert all(x["n"] == 60 for x in r)
    assert [x["acuracia"] for x in r] == [pytest.approx(54 / 60), pytest.approx(57 / 60), 1.0, 1.0]
    assert len(gravado) == 4 and {g[2] for g in gravado} == {60}


def test_validar_exige_previsoes_para_todas_as_rotuladas(tmp_path):
    rot, prev = tmp_path / "rot.csv", tmp_path / "prev.csv"
    rot.write_text("conversa_id,tema_vinicius,recusa_vinicius\n1,programação/TI,não\n2,programação/TI,não\n", encoding="utf-8")
    prev.write_text("conversa_id,classificador,versao,tema,recusa\n1,regras,1|1,programação/TI,false\n", encoding="utf-8")
    with pytest.raises(ValueError, match="não cobrem"):
        validacao.validar(None, rot, prev)
