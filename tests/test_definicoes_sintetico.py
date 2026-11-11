"""T-109: contrato das definições na base sintética (verdade conhecida em tests/esperado.py, escrita à mão).

Um teste por caso (A..K). O parâmetro diz em uma linha a regra de definição que o caso protege; se ele quebrar, a
definição do indicador mudou. A carga + transformação do sintético roda uma vez por sessão (conftest.py).
Totais, limiares e agregados continuam em test_transformar.py e test_agregados.py.
"""
import psycopg
import pytest

import esperado
from loader import migrar, transformar

REGRA = {
    "A": "retorno = outra sessão com início <= 168 h após o início da 1ª (6 d 23 h conta)",
    "B": "retorno fora da janela de 168 h (7 d + 1 min) não conta",
    "C": "gap <= 30 min entre o FIM de uma conversa e o INÍCIO da seguinte = mesma sessão, não é retorno",
    "D": "usuário = IP + família de SO e navegador, sem versão: versão nova do navegador é o MESMO usuário",
    "E": "IP com >= 10 user-agents é tráfego anômalo: fora da análise (inelegível)",
    "F": "conversa só com pergunta vazia não conta como uso e não gera usuário",
    "F2": "pergunta vazia não é retorno (não conta como uso)",
    "G": "1ª sessão nos últimos 7 dias da base = coorte imatura (inelegível)",
    "H": "1ª sessão nos primeiros 14 dias da base = burn-in (inelegível)",
    "I": "conversa sem resposta do assistente é rejeitada na carga",
    "J": "controle: usuário maduro, fora do burn-in e sem anomalia é elegível e não voltou",
    "K": "mesmo IP com SO/navegador diferentes = 2 usuários oficiais (e 1 só pela chave só-IP)",
}


def _q(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args or None).fetchall()


def test_todo_caso_tem_regra():
    assert set(REGRA) == set(esperado.CASOS)


@pytest.mark.usefixtures("usar_sint")
@pytest.mark.parametrize("codigo", sorted(esperado.CASOS))
def test_caso(codigo):
    caso, regra = esperado.CASOS[codigo], REGRA[codigo]
    ips = list(caso.hashed_ips)
    # carga: conversas carregadas (a rejeitada do caso I não entra em stg) e as que não contam como uso
    carregadas, nao_uso = _q("SELECT count(*), count(*) FILTER (WHERE NOT conta_como_uso) FROM stg.conversa "
                             "WHERE hashed_ip = ANY(%s)", ips)[0]
    assert (carregadas, nao_uso) == (caso.n_conversas - caso.n_rejeitadas, caso.n_nao_uso), regra
    # usuários, sessões e flags
    usuarios = [r[0] for r in _q(
        "SELECT DISTINCT usuario_id FROM stg.conversa WHERE hashed_ip = ANY(%s) AND conta_como_uso", ips)]
    assert len(usuarios) == caso.usuarios_oficiais, regra
    assert _q("SELECT count(DISTINCT usuario_id_ip) FROM stg.conversa WHERE hashed_ip = ANY(%s) AND conta_como_uso",
              ips)[0][0] == caso.usuarios_so_ip, regra
    if not usuarios:
        assert caso.elegivel is None, regra
        return
    assert _q("SELECT count(*) FROM mart.fct_sessao WHERE usuario_id = ANY(%s)", usuarios)[0][0] == caso.sessoes, regra
    linhas = _q("SELECT d.elegivel, d.motivo_inelegivel, f.voltou_7d FROM mart.dim_usuario d "
                "JOIN mart.fct_primeira_experiencia f USING (usuario_id) WHERE usuario_id = ANY(%s)", usuarios)
    assert len(linhas) == len(usuarios), regra
    for elegivel, motivo, voltou in linhas:
        assert elegivel is caso.elegivel, f"caso {codigo}: elegivel={elegivel}. Regra: {regra}"
        assert motivo == caso.motivo_inelegivel, f"caso {codigo}: motivo={motivo}. Regra: {regra}"
        assert voltou is caso.voltou_7d, f"caso {codigo}: voltou_7d={voltou}. Regra: {regra}"


# ---------------------------------------------------------------- bordas inclusivas (o sintético não tem caso na borda)
# Muda stg DENTRO de uma transação, roda os SQL de transformação nela e desfaz tudo: nada fica no banco.
def _na_borda(deslocar_minutos: int, codigo: str):
    """Desloca a 2ª conversa do caso (início e fim) e devolve (sessões do usuário, voltou_7d, voltaram da calc_retencao)."""
    with psycopg.connect(migrar.dsn()) as c:
        try:
            c.execute("UPDATE stg.conversa SET ts_inicio = ts_inicio + make_interval(mins => %s), "
                      "ts_fim = ts_fim + make_interval(mins => %s) WHERE conversa_id = ("
                      "SELECT conversa_id FROM stg.conversa WHERE hashed_ip = %s ORDER BY ts_inicio DESC LIMIT 1)",
                      (deslocar_minutos, deslocar_minutos, esperado.ip(codigo)))
            for arq in transformar.arquivos():
                c.execute(arq.read_text(encoding="utf-8"))
            uid = c.execute("SELECT usuario_id FROM stg.conversa WHERE hashed_ip = %s LIMIT 1", (esperado.ip(codigo),)).fetchone()[0]
            sessoes = c.execute("SELECT count(*) FROM mart.fct_sessao_novo WHERE usuario_id = %s", (uid,)).fetchone()[0]
            voltou = c.execute("SELECT voltou_7d FROM mart.fct_primeira_experiencia_novo WHERE usuario_id = %s", (uid,)).fetchone()[0]
            vol_calc = c.execute("SELECT voltaram_7d FROM mart.calc_retencao('oficial')").fetchone()[0]
            return sessoes, voltou, vol_calc
        finally:
            c.rollback()


@pytest.mark.usefixtures("usar_sint")
@pytest.mark.parametrize("minutos,voltou,voltaram", [
    (-1, True, esperado.RETORNOS_ENTRE_ELEGIVEIS + 1),
    (0, False, esperado.RETORNOS_ENTRE_ELEGIVEIS),
], ids=["retorno_em_exatamente_168h_conta", "retorno_em_168h_mais_1min_nao_conta"])
def test_borda_da_janela_de_retorno_e_inclusiva(minutos, voltou, voltaram):
    """Caso B (retorno em 7 d + 1 min): -1 min o põe em exatamente 168 h (conta: <=); sem deslocar, fica fora."""
    sessoes, voltou_7d, vol_calc = _na_borda(minutos, "B")
    assert (sessoes, voltou_7d, vol_calc) == (2, voltou, voltaram)


@pytest.mark.usefixtures("usar_sint")
@pytest.mark.parametrize("minutos,sessoes", [(10, 1), (11, 2)],
                         ids=["gap_de_exatamente_30min_e_mesma_sessao", "gap_de_31min_abre_nova_sessao"])
def test_borda_do_gap_de_sessao_e_inclusiva(minutos, sessoes):
    """Caso C (2ª conversa 20 min após o FIM da 1ª): +10 min = exatamente 30 min (mesma sessão: <=); +11 = 31 min (nova)."""
    assert _na_borda(minutos, "C")[0] == sessoes
