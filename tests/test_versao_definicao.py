"""T-109: a definição de indicador não muda sem um teste quebrar.

`tests/referencia_definicao.json` guarda, por versão, os valores de ops.parametros e os números-âncora do snapshot.
  - mudar um parâmetro SEM subir `versao_definicao`  -> falha (valor diferente da referência da versão corrente);
  - subir `versao_definicao` SEM acrescentar a referência -> falha (versão sem referência).
A comparação é uma função pura (`verificar`), testada em separado com os dois cenários; o teste de banco aplica-a
aos parâmetros reais do compose.
"""
import json
from pathlib import Path

import psycopg
import pytest

from loader import migrar

REFERENCIA = Path(__file__).with_name("referencia_definicao.json")
AVISO = "Se você mudou a definição de propósito, suba a versão (nova migração em ops.parametros) e acrescente-a a tests/referencia_definicao.json."


def carregar_referencia() -> dict:
    return {k: v for k, v in json.loads(REFERENCIA.read_text(encoding="utf-8")).items() if not k.startswith("_")}


def verificar(parametros: dict[str, str], referencia: dict) -> list[str]:
    """Problemas entre os parâmetros do banco e a referência da versão corrente (lista vazia = tudo certo)."""
    versao = parametros.get("versao_definicao")
    if versao not in referencia:
        return [f"versao_definicao={versao!r} não tem referência em referencia_definicao.json "
                f"(versões conhecidas: {sorted(referencia)}). {AVISO}"]
    esperado = referencia[versao]["parametros"]
    atual = {k: v for k, v in parametros.items() if k != "versao_definicao"}
    problemas = []
    for chave in sorted(set(esperado) | set(atual)):
        if esperado.get(chave) != atual.get(chave):
            problemas.append(f"parâmetro {chave!r}: referência da v{versao} = {esperado.get(chave)!r}, banco = {atual.get(chave)!r} "
                             f"sem subir versao_definicao. {AVISO}")
    return problemas


# ------------------------------------------------------------------ a função, com os dois cenários de falha
PARAMS_V1 = {"versao_definicao": "1.0.0", **{k: str(v) for k, v in carregar_referencia()["1.0.0"]["parametros"].items()}}


def test_verificar_aceita_a_versao_corrente_igual_a_referencia():
    assert verificar(PARAMS_V1, carregar_referencia()) == []


def test_verificar_pega_parametro_mudado_sem_subir_a_versao():
    problemas = verificar({**PARAMS_V1, "gap_sessao_min": "60"}, carregar_referencia())
    assert len(problemas) == 1 and "gap_sessao_min" in problemas[0] and "'60'" in problemas[0]


def test_verificar_pega_versao_nova_sem_referencia():
    problemas = verificar({**PARAMS_V1, "versao_definicao": "1.1.0"}, carregar_referencia())
    assert len(problemas) == 1 and "1.1.0" in problemas[0] and "não tem referência" in problemas[0]


def test_verificar_aceita_versao_nova_com_referencia_acrescentada():
    ref = carregar_referencia()
    ref["1.1.0"] = {"parametros": {**ref["1.0.0"]["parametros"], "gap_sessao_min": "60"}}
    assert verificar({**PARAMS_V1, "versao_definicao": "1.1.0", "gap_sessao_min": "60"}, ref) == []


def test_verificar_pega_parametro_novo_ou_removido():
    sem = {k: v for k, v in PARAMS_V1.items() if k != "n_minimo"}
    assert any("n_minimo" in p for p in verificar(sem, carregar_referencia()))
    assert any("novo_limiar" in p for p in verificar({**PARAMS_V1, "novo_limiar": "1"}, carregar_referencia()))


# ------------------------------------------------------------------ o banco do compose
def test_parametros_do_banco_batem_com_a_referencia():
    migrar.migrar()
    with psycopg.connect(migrar.dsn()) as c:
        parametros = dict(c.execute("SELECT chave, valor FROM ops.parametros").fetchall())
    problemas = verificar(parametros, carregar_referencia())
    assert not problemas, "\n".join(problemas)
