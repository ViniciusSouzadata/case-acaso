"""T-205: provedor `regras`, provedores com LLM (resposta simulada, sem rede), fábrica por configuração e contrato do seed."""
import csv
from pathlib import Path

import psycopg
import pytest

from classificador import tema
from classificador.tema import INDEFINIDO, PROMPT_SISTEMA, TAXONOMIA, TRUNCAR_EM
from loader.migrar import dsn

SEED = Path(tema.SAIDA_PADRAO)


# ----------------------------------------------------------------------------------------------- regras
@pytest.fixture(scope="module")
def regras():
    return tema.ProvedorRegras()


@pytest.mark.parametrize("pergunta, esperado", [
    ("Escreva um código em Python que ordene uma lista", "programação/TI"),
    ("Faça um resumo do capítulo sobre fotossíntese para a prova de biologia", "estudo/dever de casa"),
    ("Traduza para o inglês: bom dia", "escrita e tradução"),
    ("Preciso de um plano de negócio para minha empresa de marketing", "trabalho/negócios"),
    ("Escreva uma história de fantasia com um dragão e seu personagem principal", "criação/ficção e roleplay"),
    ("Oi, tudo bem? Estou triste hoje", "conversa pessoal/conselho"),
    ("Qual a capital da Austrália?", "informação geral/curiosidade"),
    ("asdf qwer", INDEFINIDO),
    ("", INDEFINIDO),
    ("REDAÇÃO sobre o ENEM", "estudo/dever de casa"),   # sem diferença de acento nem de caixa
    ("Quero um molho apimentado", INDEFINIDO),            # "api$" só casa a palavra inteira
])
def test_regras_casos_feitos_a_mao(regras, pergunta, esperado):
    assert regras.classificar(pergunta) == esperado


def test_regras_so_olham_o_trecho_truncado(regras):
    assert regras.classificar("x" * TRUNCAR_EM + " python") == INDEFINIDO
    assert regras.classificar("x" * (TRUNCAR_EM - 8) + " python") == "programação/TI"


def test_empate_vai_para_o_primeiro_da_lista(tmp_path):
    arq = tmp_path / "regras.yaml"
    arq.write_text('versao: "9.9.9"\ntemas:\n  - {tema: "programação/TI", palavras: [alfa]}\n'
                   '  - {tema: "estudo/dever de casa", palavras: [beta]}\n', encoding="utf-8")
    p = tema.ProvedorRegras(arq)
    assert p.classificar("alfa e beta") == "programação/TI" and p.versao_prompt == "9.9.9"


def test_todos_os_rotulos_das_regras_estao_na_taxonomia(regras):
    assert {t for t, _ in regras._regras} <= set(TAXONOMIA)


# ----------------------------------------------------------------------------------------------- LLM (simulado)
def test_extrair_tema():
    assert tema.extrair_tema('{"tema": "programação/TI"}') == "programação/TI"
    assert tema.extrair_tema('Claro! {"tema": "escrita e tradução"} ok') == "escrita e tradução"
    assert tema.extrair_tema('{"tema": "culinária"}') is None       # fora da taxonomia
    assert tema.extrair_tema("sem json") is None and tema.extrair_tema("{quebrado") is None and tema.extrair_tema("") is None


def test_llm_envia_so_o_trecho_truncado_e_o_prompt_com_a_taxonomia():
    vistos = []

    def chamar(sistema, pergunta):
        vistos.append((sistema, pergunta))
        return '{"tema": "trabalho/negócios"}'

    p = tema.ProvedorBedrock("modelo-x", chamar=chamar)
    assert p.classificar("a" * 5000) == "trabalho/negócios"
    sistema, enviado = vistos[0]
    assert len(enviado) == TRUNCAR_EM and sistema == PROMPT_SISTEMA
    assert all(t in sistema for t in TAXONOMIA)


def test_llm_tenta_de_novo_uma_vez_e_depois_cai_em_indefinido():
    respostas = iter(["lixo", '{"tema": "estudo/dever de casa"}'])
    p = tema.ProvedorBedrock("m", chamar=lambda s, q: next(respostas))
    assert p.classificar("oi") == "estudo/dever de casa"
    chamadas = []
    p2 = tema.ProvedorAnthropic("m", chamar=lambda s, q: chamadas.append(1) or '{"tema": "inventado"}')
    assert p2.classificar("oi") == INDEFINIDO and len(chamadas) == 2


def test_origem_do_seed_identifica_provedor_e_modelo():
    assert tema.tema_origem(tema.ProvedorBedrock("modelo-x", chamar=lambda s, q: "")) == "bedrock:modelo-x"
    assert tema.tema_origem(tema.ProvedorRegras()).startswith("regras:")


# ----------------------------------------------------------------------------------------------- fábrica
def test_sem_configuracao_o_padrao_e_regras_sem_credencial():
    assert isinstance(tema.criar_provedor(env={}), tema.ProvedorRegras)
    assert isinstance(tema.criar_provedor(env={"TEMA_PROVEDOR": "regras"}), tema.ProvedorRegras)


def test_bedrock_sem_modelo_configurado_falha_com_mensagem_clara():
    with pytest.raises(RuntimeError, match="TEMA_BEDROCK_MODELO"):
        tema.criar_provedor("bedrock", env={})


def test_anthropic_sem_chave_falha_e_provedor_desconhecido_tambem():
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        tema.criar_provedor("anthropic", env={})
    with pytest.raises(ValueError, match="desconhecido"):
        tema.criar_provedor("outro", env={})


def test_anthropic_com_chave_cria_provedor_sem_chamar_a_rede():
    p = tema.criar_provedor("anthropic", env={"ANTHROPIC_API_KEY": "chave-de-teste"})
    assert isinstance(p, tema.ProvedorAnthropic) and p.modelo


# ----------------------------------------------------------------------------------------------- contrato do seed
def _seed():
    with SEED.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_contrato_do_seed():
    linhas = _seed()
    assert list(linhas[0].keys()) == tema.CABECALHO
    ids = [l["conversa_id"] for l in linhas]
    assert len(ids) == len(set(ids)) and all(i.isdigit() for i in ids)
    assert {l["tema"] for l in linhas} <= set(TAXONOMIA)
    assert all(l["tema_origem"] and l["versao_prompt"] for l in linhas)


@pytest.mark.usefixtures("usar_real")
def test_seed_cobre_todas_as_conversas_que_contam_como_uso_e_a_carga_junta():
    seed = {int(l["conversa_id"]): l for l in _seed()}
    with psycopg.connect(dsn(), autocommit=True) as c:
        uso = {r[0]: (r[1], r[2]) for r in c.execute(
            "SELECT conversa_id, tema, tema_origem FROM stg.conversa WHERE conta_como_uso")}
        sem_seed = c.execute("SELECT count(*) FROM stg.conversa WHERE NOT conta_como_uso AND tema <> 'não classificado'").fetchone()[0]
    assert set(uso) == set(seed)
    assert all(uso[i] == (seed[i]["tema"], seed[i]["tema_origem"]) for i in seed)
    assert "não classificado" not in {t for t, _ in uso.values()} and sem_seed == 0
