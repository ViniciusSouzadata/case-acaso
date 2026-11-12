"""T-503: regressão do incidente §4.2. A chave `hashed_ip|user-agent` inflava "usuários novos"; a oficial não pode.

Base sintética (tests/esperado.py):
  caso D: mesma pessoa, Chrome 120 -> Chrome 121 (troca de versão do navegador) -> UM usuário pela chave oficial;
  caso E: 1 IP com 12 user-agents -> tráfego anômalo: nenhum desses usuários entra nos "novos" da análise.
O terceiro teste prova que o teste pega o defeito: com a chave do incidente, a invariante do caso D quebra.
"""
import psycopg
import pytest

import esperado
from loader import migrar

OFICIAL, INCIDENTE = "usuario_id", "usuario_id_ip_ua"


def _um(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args).fetchone()


def _usuarios_do_ip(coluna: str, caso: str) -> int:
    """Quantos 'usuários' a chave distingue num IP (só conversas que contam como uso)."""
    assert coluna in (OFICIAL, INCIDENTE, "usuario_id_ip")
    return _um(f"SELECT count(DISTINCT {coluna}) FROM stg.conversa WHERE hashed_ip = %s AND conta_como_uso",  # noqa: S608 - coluna validada acima
               esperado.ip(caso))[0]


def _troca_de_versao_nao_cria_usuario(coluna: str) -> bool:
    return _usuarios_do_ip(coluna, "D") == esperado.CASOS["D"].usuarios_oficiais == 1


@pytest.mark.usefixtures("usar_sint")
class TestRegressaoIncidente:
    def test_troca_de_versao_do_navegador_nao_infla_novos_pela_chave_oficial(self):
        assert _usuarios_do_ip(OFICIAL, "D") == 1
        assert _troca_de_versao_nao_cria_usuario(OFICIAL)
        n_dim = _um("SELECT count(*) FROM mart.dim_usuario d WHERE d.usuario_id IN "
                    "(SELECT usuario_id FROM stg.conversa WHERE hashed_ip = %s)", esperado.ip("D"))[0]
        assert n_dim == 1

    def test_ip_com_12_user_agents_nao_entra_nos_novos_da_analise(self):
        ip_e = esperado.ip("E")
        assert _usuarios_do_ip(INCIDENTE, "E") == 12             # a chave do incidente fabricaria 12 "novos" de um IP só
        elegiveis, anomalos = _um(
            "SELECT count(*) FILTER (WHERE d.elegivel), count(*) FILTER (WHERE d.trafego_anomalo) FROM mart.dim_usuario d "
            "WHERE d.usuario_id IN (SELECT usuario_id FROM stg.conversa WHERE hashed_ip = %s)", ip_e)
        assert elegiveis == 0 and anomalos == 12                  # na oficial: nenhum elegível, todos marcados como tráfego anômalo
        assert _um("SELECT count(*) FROM stg.conversa WHERE hashed_ip = %s", ip_e)[0] == esperado.CASOS["E"].n_conversas == 12

    def test_com_a_chave_do_incidente_o_teste_falharia(self):
        # É isto que protege contra a volta do defeito: trocar a chave oficial por `hashed_ip|user-agent` quebra a invariante do caso D.
        assert _usuarios_do_ip(INCIDENTE, "D") == 2               # Chrome 120 e Chrome 121 viram duas "pessoas"
        assert not _troca_de_versao_nao_cria_usuario(INCIDENTE)
