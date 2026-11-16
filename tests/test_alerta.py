"""Alerta de divergência: regras puras (sem banco), demonstração sem credencial e limiares vindos de ops.parametros."""
from pathlib import Path

import pytest

from loader import alerta
from loader.alerta import Limiares, detectar_saltos

LIM = Limiares(desvios=3.0, janela=8, min_historico=4)
RAIZ = Path(__file__).resolve().parent.parent


def _serie(valores):
    return [(f"S{i:02d}", float(v)) for i, v in enumerate(valores)]


def test_serie_estavel_nao_alerta():
    assert detectar_saltos(_serie([100, 104, 98, 101, 99, 103, 97, 102]), LIM, "novos_por_semana", "novos") == []


def test_salto_acima_da_variacao_normal_alerta():
    r = detectar_saltos(_serie([100, 104, 98, 101, 99, 103, 97, 210]), LIM, "novos_por_semana", "novos")
    assert len(r) == 1 and r[0].detalhe.startswith("S07") and "210" in r[0].detalhe


def test_queda_tambem_conta():
    assert len(detectar_saltos(_serie([100, 104, 98, 101, 99, 20]), LIM, "novos_por_semana", "novos")) == 1


def test_sem_historico_minimo_nao_avalia():
    assert detectar_saltos(_serie([100, 104, 500]), LIM, "novos_por_semana", "novos") == []


def test_limiar_maior_silencia_o_mesmo_salto():
    s = _serie([100, 104, 98, 101, 99, 103, 97, 210])
    assert detectar_saltos(s, Limiares(100.0, 8, 4), "x", "novos") == []


def test_serie_constante_nao_alarma_por_ruido_minimo():
    assert detectar_saltos(_serie([50, 50, 50, 50, 51]), LIM, "x", "novos") == []


def test_reconciliacao_alerta_so_metrica_fora_da_tolerancia():
    r = alerta.avaliar_reconciliacao([("a", 10, 10, True), ("b", 10, 12, False)])
    assert [x.regra for x in r] == ["reconciliacao"] and r[0].detalhe.startswith("b:")


def test_aviso_traz_so_agregados():
    lim, reconc, novos, uas = alerta._demo()
    aviso = alerta.montar_aviso(alerta.avaliar(reconc, novos, uas, lim))
    for proibido in ("hashed_ip", "user_agent", "Mozilla", "conversation"):
        assert proibido not in aviso
    assert aviso.startswith("ALERTA: 3 divergência(s)")


def test_demo_roda_sem_banco_nem_credencial(monkeypatch, capsys):
    for k in ("PGHOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert alerta.main(["--demo"]) == 2
    saida = capsys.readouterr().out
    assert "[reconciliacao]" in saida and "[novos_por_semana]" in saida and "[uas_por_ip]" in saida


def test_arquivo_de_alerta_opcional(monkeypatch, tmp_path):
    destino = tmp_path / "alertas.log"
    monkeypatch.setenv("ALERTA_ARQUIVO", str(destino))
    alerta.main(["--demo"])
    assert destino.read_text(encoding="utf-8").startswith("ALERTA:")


def test_limiares_nao_estao_escritos_no_codigo():
    # os valores de produção (3, 8, 4) só aparecem na migração; no módulo, só na demonstração e como nomes de parâmetro
    fonte = (RAIZ / "loader" / "alerta.py").read_text(encoding="utf-8")
    assert "alerta_desvios" in fonte and "alerta_janela_semanas" in fonte and "alerta_min_historico" in fonte
    migracao = (RAIZ / "sql" / "migrations" / "021_alerta_parametros.sql").read_text(encoding="utf-8")
    assert "'alerta_desvios',         '3'" in migracao


@pytest.mark.usefixtures("usar_sint")
def test_modo_banco_le_limiares_de_ops_parametros(capsys):
    # no banco sintético migrado, o alerta roda e devolve texto de agregados
    codigo = alerta.main([])
    saida = capsys.readouterr().out
    assert codigo in (0, 2) and saida.startswith("ALERTA:")
    assert "hashed_ip" not in saida and "Mozilla" not in saida


def test_so_a_ultima_semana_e_avaliada_por_padrao():
    s = _serie([100, 104, 98, 101, 99, 103, 210, 100, 101])  # salto no meio, última semana normal
    assert detectar_saltos(s, LIM, "x", "novos") == []
    assert len(detectar_saltos(s, Limiares(3.0, 8, 4, avaliadas=0), "x", "novos")) == 1  # retrospectiva pega


def test_contagem_pequena_nao_alarma_por_ruido_natural():
    # média 25, desvio de 1; sem o piso (raiz da média = 5) 33 seria alarme; com ele, não
    assert detectar_saltos(_serie([25, 26, 24, 25, 25, 26, 24, 33]), LIM, "x", "novos") == []
