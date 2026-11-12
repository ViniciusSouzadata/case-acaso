"""T-209: achados válidos, encadeamento e reprodutibilidade (duas execuções, mesmo resultado)."""
import psycopg
import pytest

from analise import achados, ajustado, bruto, meta, propensao, semana, sensibilidade
from analise import __main__ as principal
from loader.migrar import dsn

TABELAS = ["meta", "efeito_fator", "balanco_propensao", "decomposicao_semana", "decomposicao_resumo", "sensibilidade_efeito", "achado"]


def test_achados_do_seed_sao_validos():
    dados = achados.ler()
    assert [a["ordem"] for a in dados] == [1, 2, 3]
    for a in dados:
        assert all(str(a[c]).strip() for c in achados.COLUNAS)


def test_achados_sem_buraco_na_ordem(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("- {ordem: 2, titulo: t, evidencia: e, decisao: d, limite: l}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ordem"):
        achados.ler(f)


def test_tudo_chama_as_etapas_em_ordem(monkeypatch):
    chamadas = []
    monkeypatch.setattr(principal, "main", lambda argv: chamadas.append(argv[0]) or 0)
    assert principal.tudo() == 0
    assert chamadas[:7] == ["meta", "eda", "bruto", "ajustado", "semana", "propensao", "sensibilidade"]
    assert chamadas[-1] == "achados" and chamadas.count("validacao") <= 1


def test_tudo_para_na_primeira_falha(monkeypatch):
    chamadas = []
    monkeypatch.setattr(principal, "main", lambda argv: chamadas.append(argv[0]) or (1 if argv[0] == "bruto" else 0))
    assert principal.tudo() == 1 and chamadas[-1] == "bruto"


def _foto(c):
    out = {}
    for t in TABELAS:
        linhas = c.execute(f"SELECT * FROM resultado.{t}").fetchall()  # noqa: S608 - nomes fixos acima
        out[t] = sorted(map(repr, linhas))
    return out


@pytest.mark.usefixtures("usar_real")
def test_duas_execucoes_dao_o_mesmo_resultado():
    def rodar(c):
        meta.gravar(c)
        bruto.gravar(c)
        ajustado.gravar(c)
        semana.gravar(c, None)
        propensao.gravar(c)
        sensibilidade.gravar(c)
        achados.gravar(c)
        return _foto(c)

    with psycopg.connect(dsn(), autocommit=True) as c:
        a = rodar(c)
        b = rodar(c)
        assert all(len(v) > 0 for v in a.values())
    for t in TABELAS:
        if t == "meta":   # a data/hora da gravação muda; o resto da linha não
            continue
        assert a[t] == b[t], t
