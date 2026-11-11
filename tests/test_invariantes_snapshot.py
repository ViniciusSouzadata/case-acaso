"""T-109: invariantes do snapshot real versionado. Números-âncora = definição v1.0.0 + snapshot versionado
(tests/referencia_definicao.json). Se algum quebrar, ou o snapshot ou a definição mudou."""
import json
from pathlib import Path

import psycopg
import pytest

from loader import carregar, migrar

SNAPSHOT = Path(carregar.SNAPSHOT)
REF = json.loads(Path(__file__).with_name("referencia_definicao.json").read_text(encoding="utf-8"))
VERSAO = "1.0.0"
A = REF[VERSAO]["ancoras_snapshot"]
AVISO = (f"Os números-âncora são da definição v{VERSAO} e do snapshot versionado. "
         "Se você mudou a definição de propósito, suba a versão e atualize a referência (tests/referencia_definicao.json).")

pytestmark = [pytest.mark.skipif(not SNAPSHOT.is_file(), reason="snapshot real ausente"),
              pytest.mark.usefixtures("usar_real")]


def _q(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args or None).fetchall()


def _um(sql, *args):
    return _q(sql, *args)[0]


def _igual(obtido, esperado, nome):
    assert obtido == esperado, f"{nome}: obtido {obtido}, esperado {esperado}. {AVISO}"


def test_versao_corrente_e_a_da_referencia():
    _igual(_um("SELECT ops.param('versao_definicao')")[0], VERSAO, "versao_definicao")


def test_snapshot_e_o_versionado():
    sha = Path(str(SNAPSHOT.with_suffix(".sha256"))).read_text().split()[0]
    _igual(sha, A["snapshot_sha256"], "sha256 do snapshot")


def test_11621_conversas_e_conversa_id_unico():
    total, distintos = _um("SELECT count(*), count(DISTINCT conversa_id) FROM stg.conversa")
    _igual(total + _um("SELECT count(*) FROM ops.rejeitado")[0], A["conversas"], "conversas lidas (stg + rejeitadas)")
    _igual(total, A["conversas"] - A["rejeitadas"], "conversas em stg")
    _igual(distintos, total, "conversa_id distintos (devia ser único)")


def test_voltaram_nao_excedem_novos_em_todo_periodo_e_segmento():
    for tabela, chave in (("agg_retencao_periodo", "granularidade, periodo"),
                          ("agg_retencao_segmento", "variavel, valor"),
                          ("agg_retencao_sensibilidade", "definicao")):
        ruins = _q(f"SELECT {chave} FROM mart.{tabela} WHERE voltaram_7d > {'usuarios' if 'sensib' in tabela else 'novos'}")
        assert ruins == [], f"{tabela}: voltaram_7d > novos em {ruins}. {AVISO}"
    novos, voltaram = _um("SELECT count(*), count(*) FILTER (WHERE voltou_7d) FROM mart.fct_primeira_experiencia WHERE elegivel")
    assert voltaram <= novos


def test_somas_fecham_com_os_numeros_ancora():
    _igual(_um("SELECT count(*) FROM mart.dim_usuario")[0], A["usuarios_com_uso"], "usuários com uso")
    _igual(_um("SELECT count(*) FROM mart.fct_sessao")[0], A["sessoes"], "sessões")
    _igual(_um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel")[0], A["elegiveis"], "elegíveis")
    _igual(_um("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE elegivel AND voltou_7d")[0],
           A["voltaram_7d"], "voltaram em 7 dias")
    # cada variável de segmento particiona os elegíveis: as somas fecham com o global
    for variavel, novos, vol in _q("SELECT variavel, sum(novos), sum(voltaram_7d) FROM mart.agg_retencao_segmento GROUP BY 1"):
        _igual((novos, vol), (A["elegiveis"], A["voltaram_7d"]), f"soma do segmento {variavel}")
    # períodos maduros somam no máximo os elegíveis (semana parcialmente imatura fica de fora)
    for gran in ("semana", "mes"):
        novos, vol = _um("SELECT sum(novos), sum(voltaram_7d) FROM mart.agg_retencao_periodo WHERE granularidade = %s AND madura", gran)
        assert novos <= A["elegiveis"] and vol <= A["voltaram_7d"], f"{gran}: {novos}/{vol}. {AVISO}"


def test_taxa_oficial_566_de_2372():
    usuarios, vol, taxa = _um("SELECT usuarios, voltaram_7d, taxa FROM mart.agg_retencao_sensibilidade WHERE definicao = 'oficial'")
    _igual((usuarios, vol), (A["elegiveis"], A["voltaram_7d"]), "taxa oficial (elegíveis, voltaram)")
    assert float(taxa) == pytest.approx(A["voltaram_7d"] / A["elegiveis"], abs=1e-6), \
        f"taxa oficial {taxa} != {A['voltaram_7d']}/{A['elegiveis']} (23,86%). {AVISO}"
