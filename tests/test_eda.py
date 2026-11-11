"""T-202: EDA só com figura que leva a conclusão; problemas de qualidade batem com o discovery."""
from pathlib import Path

import psycopg
import pytest

from analise import eda
from loader.migrar import dsn

PASTA_COMMITADA = Path(eda.__file__).resolve().parent.parent / "docs" / "figuras"


def test_semanas_anomalas_feito_a_mao():
    # vizinhas da posição 4 (valor 20): 100,100,100,100 | 100,100,100,100 -> mediana 100 -> 20 < 50 -> anômala
    vol = [90, 100, 100, 100, 20, 100, 100, 100, 100, 5]
    assert eda.semanas_anomalas(vol) == [4]  # a última (5) é ponta parcial e não é avaliada
    assert eda.semanas_anomalas([100, 100, 100, 100]) == []
    assert eda.semanas_anomalas([100, 51, 100]) == []  # 51 não é < 50% de 100


def test_participacao_topo():
    assert eda.participacao_topo([50, 30, 10, 10], 1) == 0.5
    assert eda.participacao_topo([50, 30, 10, 10], 2) == 0.8


def test_detecta_figura_sem_conclusao(tmp_path):
    (tmp_path / "01_a.png").write_bytes(b"x")
    (tmp_path / "02_b.png").write_bytes(b"x")
    (tmp_path / "conclusoes.md").write_text("- `01_a.png`: ok\n", encoding="utf-8")
    assert eda.figuras_sem_conclusao(tmp_path) == ["02_b.png"]


def test_figuras_commitadas_tem_conclusao_e_no_maximo_seis():
    if not PASTA_COMMITADA.is_dir():
        pytest.skip("docs/figuras não montada neste ambiente")
    assert eda.figuras_sem_conclusao(PASTA_COMMITADA) == []
    assert len(list(PASTA_COMMITADA.glob("*.png"))) <= eda.MAX_FIGURAS


@pytest.mark.usefixtures("usar_real")
def test_eda_gera_figuras_com_conclusao_e_problemas_do_discovery(tmp_path, monkeypatch):
    monkeypatch.setattr(eda, "PASTA_FIGURAS", tmp_path)
    with psycopg.connect(dsn(), autocommit=True) as c:
        r = eda.gerar(c)
        tabela = {p: (n, float(f)) for p, n, f in c.execute(
            "SELECT problema, contagem, percentual FROM resultado.problema_qualidade")}
    assert 5 <= len(r["figuras"]) <= eda.MAX_FIGURAS  # com o seed de tema, as 6 figuras
    assert eda.figuras_sem_conclusao(tmp_path) == []
    assert all((tmp_path / n).stat().st_size > 5000 for n in r["figuras"])
    por_inicio = lambda ini: next(v for k, v in tabela.items() if k.startswith(ini))  # noqa: E731
    assert por_inicio("Pergunta vazia")[0] == 141
    assert por_inicio("Conversa sem nenhuma mensagem")[0] == 76
    assert por_inicio("Conteúdo repetido")[0] == 93
    assert por_inicio("IP muda")[0] == 175
    assert por_inicio("Conversas do IP mais ativo")[0] == 1557
    assert por_inicio("Conversas com dado pessoal")[0] == 56
    assert por_inicio("Conversas tóxicas")[0] == 0
    assert por_inicio("Semanas com queda")[0] >= 2  # 09/10/2023 e 05/02/2024 do discovery
    assert por_inicio("Idioma divergente em pergunta curta")[0] > 0
    assert por_inicio("Conversas do IP mais ativo")[1] == pytest.approx(1557 / 11621, abs=1e-5)
