"""T-104: integração da carga (dentro do compose, contra o Postgres). Nunca imprime texto de conversa."""
from pathlib import Path

import psycopg
import pytest

import esperado
import fabrica_bruto
from loader import carregar, migrar

SNAPSHOT = Path(carregar.SNAPSHOT)
COLUNAS_STG = {
    "conversa_id", "conversation_hash", "hash_repetido", "hashed_ip", "user_agent", "accept_language",
    "ua_so", "ua_navegador", "ua_dispositivo", "usuario_id", "usuario_id_ip", "usuario_id_ip_ua",
    "modelo_versao", "modelo_familia", "ts_inicio", "ts_fim", "n_turnos", "idioma_conversa",
    "idioma_pergunta_1", "idioma_resposta_1", "idioma_divergente", "estado", "fuso", "chars_pergunta_1",
    "chars_resposta_1", "recusa_1", "pergunta_vazia", "conta_como_uso", "ip_mudou", "redacted", "tema",
    "tema_origem", "lote_id",
}


@pytest.fixture(autouse=True)
def banco_limpo():
    migrar.migrar()
    with psycopg.connect(migrar.dsn(), autocommit=True) as c:
        c.execute("TRUNCATE stg.conversa, ops.rejeitado")


def _um(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args).fetchone()


def _contagens():
    return _um("SELECT count(*), count(DISTINCT conversa_id), sum(conta_como_uso::int) FROM stg.conversa")


@pytest.fixture(scope="module")
def sintetico(tmp_path_factory):
    return fabrica_bruto.gerar(tmp_path_factory.mktemp("sint") / "sintetico.parquet")


def test_sintetico_contagens(sintetico):
    r = carregar.carregar(sintetico)
    assert (r["lidas"], r["rejeitadas"], r["gravadas"]) == (
        esperado.CONVERSAS_GERADAS, esperado.CONVERSAS_REJEITADAS, esperado.CONVERSAS_CARREGADAS) == (52, 1, 51)
    total, distintos, usos = _contagens()
    assert (total, distintos) == (51, 51)
    assert total - usos == esperado.CONVERSAS_NAO_USO == 2
    assert _um("SELECT count(*) FROM stg.conversa WHERE hash_repetido")[0] == esperado.CONVERSAS_COM_HASH_REPETIDO
    assert _um("SELECT count(DISTINCT hashed_ip) FROM stg.conversa")[0] == esperado.IPS_DISTINTOS - 1  # I rejeitada
    assert _um("SELECT count(DISTINCT usuario_id) FROM stg.conversa WHERE conta_como_uso")[0] == esperado.USUARIOS_OFICIAIS
    assert _um("SELECT count(DISTINCT usuario_id_ip) FROM stg.conversa WHERE conta_como_uso")[0] == esperado.USUARIOS_SO_IP
    # versão nova do navegador (caso D) continua sendo o mesmo usuário oficial
    assert _um("SELECT count(DISTINCT usuario_id) FROM stg.conversa WHERE hashed_ip = %s", esperado.ip("D"))[0] == 1
    assert _um("SELECT count(DISTINCT usuario_id_ip_ua) FROM stg.conversa WHERE hashed_ip = %s", esperado.ip("D"))[0] == 2
    assert _um("SELECT motivo FROM ops.rejeitado")[0] == "sem_resposta_assistente"
    assert _um("SELECT count(*) FROM stg.conversa WHERE tema <> 'não classificado' OR tema_origem IS NOT NULL")[0] == 0


def test_sintetico_idempotente_e_lote(sintetico):
    carregar.carregar(sintetico)
    antes = _contagens()
    r2 = carregar.carregar(sintetico)
    assert _contagens() == antes
    assert _um("SELECT count(*) FROM stg.conversa WHERE lote_id = %s", r2["lote_id"])[0] == 51
    lidas, grav, rej, status = _um(
        "SELECT linhas_lidas, linhas_gravadas, linhas_rejeitadas, status FROM ops.lote_carga WHERE lote_id = %s",
        r2["lote_id"])
    assert (lidas, grav, rej, status) == (52, 51, 1, "sucesso")


def test_falha_faz_rollback_e_marca_lote(sintetico, monkeypatch):
    def explode(*a, **k):
        raise RuntimeError("falha provocada")

    monkeypatch.setattr(carregar, "_gravar_staging", explode)
    with pytest.raises(RuntimeError):
        carregar.carregar(sintetico)
    assert _contagens()[0] == 0
    assert _um("SELECT count(*) FROM ops.rejeitado")[0] == 0  # rejeitados voltam junto com os dados
    status, erro = _um("SELECT status, erro FROM ops.lote_carga ORDER BY lote_id DESC LIMIT 1")
    assert status == "falha" and "falha provocada" in erro


@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="snapshot real ausente")
def test_snapshot_real_idempotente_sem_texto():
    r = carregar.carregar()
    assert r["lidas"] == 11621 and r["gravadas"] + r["rejeitadas"] == 11621
    antes = _contagens()
    assert antes[0] == r["gravadas"] == antes[1]
    carregar.carregar()
    assert _contagens() == antes
    assert _um("SELECT count(*) FROM stg.conversa")[0] == r["gravadas"]
    lidas, grav, rej, status = _um(
        "SELECT linhas_lidas, linhas_gravadas, linhas_rejeitadas, status FROM ops.lote_carga ORDER BY lote_id DESC LIMIT 1")
    assert (lidas, grav, rej, status) == (11621, r["gravadas"], r["rejeitadas"], "sucesso")

    # esquema: só as colunas do design e nenhuma de conteúdo; valores de texto são curtos
    with psycopg.connect(migrar.dsn()) as c:
        cols = c.execute("SELECT column_name, data_type FROM information_schema.columns "
                         "WHERE table_schema = 'stg' AND table_name = 'conversa'").fetchall()
        assert {n for n, _ in cols} == COLUNAS_STG
        assert not {n for n, _ in cols} & {"content", "conteudo", "texto", "pergunta", "resposta", "mensagem"}
        for nome, tipo in cols:
            if tipo == "text":
                maior = c.execute(f"SELECT coalesce(max(length({nome})), 0) FROM stg.conversa").fetchone()[0]
                assert maior <= 1000, f"{nome} com valor de {maior} chars: parece texto de conversa"
