"""T-106: transformações (sessão, usuário, primeira experiência, calc_retencao). Dentro do compose, contra o Postgres.
Nunca imprime texto de conversa. Sintético: compara caso a caso com tests/esperado.py. Real: invariantes."""
import os
from pathlib import Path

import psycopg
import pytest

import esperado
from loader import carregar, migrar, transformar

SNAPSHOT = Path(carregar.SNAPSHOT)


def _q(sql, *args):
    with psycopg.connect(migrar.dsn()) as c:
        return c.execute(sql, args or None).fetchall()


def _um(sql, *args):
    return _q(sql, *args)[0]


# ------------------------------------------------------------------ base sintética
@pytest.mark.usefixtures("usar_sint")  # banco sintético da sessão (conftest.py): carregado e transformado uma vez
class TestSintetico:
    def test_totais(self):
        assert _um("SELECT count(*) FROM mart.dim_usuario")[0] == esperado.USUARIOS_OFICIAIS == 42
        assert _um("SELECT count(*) FROM mart.fct_sessao")[0] == esperado.SESSOES == 48
        assert _um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel")[0] == esperado.USUARIOS_ELEGIVEIS == 20
        assert _um("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE elegivel AND voltou_7d")[0] \
            == esperado.RETORNOS_ENTRE_ELEGIVEIS == 5
        assert _um("SELECT count(*) FROM mart.dim_usuario WHERE NOT elegivel")[0] == esperado.USUARIOS_INELEGIVEIS == 22

    def test_anomalo_so_no_caso_e(self):
        n_anom = _um("SELECT count(*) FROM mart.dim_usuario WHERE trafego_anomalo")[0]
        assert n_anom == esperado.CASOS["E"].usuarios_oficiais == 12

    def test_calc_retencao_oficial_igual_aos_marts(self):
        usuarios, voltaram, taxa = _um("SELECT * FROM mart.calc_retencao('oficial')")
        el, vo = _um("SELECT count(*), count(*) FILTER (WHERE voltou_7d) FROM mart.fct_primeira_experiencia WHERE elegivel")
        assert (usuarios, voltaram) == (el, vo) == (20, 5)
        assert float(taxa) == pytest.approx(5 / 20)

    def test_calc_retencao_ip_sem_filtros(self):
        # Sem burn-in e com anômalos: 30 usuários por IP no total (usuario_id_ip distintos com uso);
        # o filtro de maturidade é parte fixa da função, então os 5 IPs imaturos (G, f17-f20) ficam de fora -> 25.
        assert _um("SELECT count(DISTINCT usuario_id_ip) FROM stg.conversa WHERE conta_como_uso")[0] \
            == esperado.USUARIOS_SO_IP == 30
        usuarios, _, _ = _um("SELECT * FROM mart.calc_retencao('ip', NULL, NULL, false, true, NULL)")
        assert usuarios == 25
        com_burn_in, _, _ = _um("SELECT * FROM mart.calc_retencao('ip', NULL, NULL, true, true, NULL)")
        assert com_burn_in == 25 - 5  # H e f01-f04 saem com o burn-in

    def test_calc_retencao_chave_invalida(self):
        with pytest.raises(psycopg.errors.RaiseException):
            _q("SELECT * FROM mart.calc_retencao('xyz')")

    def test_limiares_vem_de_ops_parametros(self):
        """gap 30 -> 10: a conversa do caso C (20 min depois) vira 2ª sessão; sai de ops.parametros, não do SQL."""
        try:
            with psycopg.connect(migrar.dsn(), autocommit=True) as c:
                c.execute("UPDATE ops.parametros SET valor = '10' WHERE chave = 'gap_sessao_min'")
            transformar.transformar()
            assert _um("SELECT count(*) FROM mart.fct_sessao")[0] == esperado.SESSOES + 1
            assert _um("SELECT usuarios FROM mart.calc_retencao('oficial')")[0] == 20
        finally:
            with psycopg.connect(migrar.dsn(), autocommit=True) as c:
                c.execute("UPDATE ops.parametros SET valor = '30' WHERE chave = 'gap_sessao_min'")
            transformar.transformar()
        assert _um("SELECT count(*) FROM mart.fct_sessao")[0] == esperado.SESSOES


# ------------------------------------------------------------------ permissões e atomicidade
@pytest.mark.usefixtures("usar_sint")
class TestSwap:
    def test_app_ro_le_marts_novos_e_nao_le_stg(self):
        dsn = (f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} dbname={os.environ['POSTGRES_DB']} "
               f"user=app_ro password={os.environ['APP_RO_PASSWORD']}")
        with psycopg.connect(dsn) as c:
            for tabela in ("fct_sessao", "dim_usuario", "dim_era_modelo", "fct_primeira_experiencia"):
                assert c.execute(f"SELECT count(*) FROM mart.{tabela}").fetchone()[0] > 0
        with psycopg.connect(dsn) as c:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute("SELECT count(*) FROM stg.conversa")

    def test_sem_tabela_novo_sobrando_e_chave_primaria_renomeada(self):
        assert _q("SELECT tablename FROM pg_tables WHERE schemaname = 'mart' AND tablename LIKE '%\\_novo'") == []
        indices = {r[0] for r in _q("SELECT indexname FROM pg_indexes WHERE schemaname = 'mart'")}
        assert {"fct_sessao_pkey", "dim_usuario_pkey", "fct_primeira_experiencia_pkey", "dim_era_modelo_pkey"} <= indices

    def test_falha_no_meio_nao_toca_os_marts(self, tmp_path):
        antes = _um("SELECT count(*) FROM mart.dim_usuario")[0]
        (tmp_path / "10_ok.sql").write_text(
            "DROP TABLE IF EXISTS mart.dim_usuario_novo; CREATE TABLE mart.dim_usuario_novo AS SELECT 1 AS x;")
        (tmp_path / "20_quebra.sql").write_text("SELECT 1/0;")
        with pytest.raises(psycopg.errors.DivisionByZero):
            transformar.transformar(tmp_path)
        assert _um("SELECT count(*) FROM mart.dim_usuario")[0] == antes
        assert _q("SELECT tablename FROM pg_tables WHERE schemaname = 'mart' AND tablename LIKE '%\\_novo'") == []

    def test_eras(self):
        eras = _q("SELECT era FROM mart.dim_era_modelo ORDER BY inicio")
        assert [e[0] for e in eras] == ["2023-04..06 (3.5 + 4 opcional)", "2023-07..10 (só 3.5)",
                                         "2023-11 (4 volta)", "2023-12+ (4 padrão)"]
        # a base sintética é de 2024-01..03: tudo na era 2023-12+
        assert _q("SELECT DISTINCT era_modelo FROM mart.fct_primeira_experiencia") == [("2023-12+ (4 padrão)",)]


# ------------------------------------------------------------------ snapshot real
@pytest.mark.skipif(not SNAPSHOT.is_file(), reason="snapshot real ausente")
@pytest.mark.usefixtures("usar_real")  # banco real da sessão (conftest.py), montado em paralelo uma única vez
class TestReal:
    def test_uma_linha_por_usuario(self):
        com_uso = _um("SELECT count(DISTINCT usuario_id) FROM stg.conversa WHERE conta_como_uso")[0]
        todos = _um("SELECT count(DISTINCT usuario_id) FROM stg.conversa")[0]
        assert todos == 2530 and com_uso <= todos
        n_dim, n_dim_distintos = _um("SELECT count(*), count(DISTINCT usuario_id) FROM mart.dim_usuario")
        n_fpe, n_fpe_distintos = _um("SELECT count(*), count(DISTINCT usuario_id) FROM mart.fct_primeira_experiencia")
        assert n_dim == n_dim_distintos == n_fpe == n_fpe_distintos == com_uso
        assert _um("SELECT count(*) FROM mart.fct_sessao WHERE seq = 1")[0] == n_dim

    def test_sessoes_consistentes(self):
        assert _um("SELECT sum(n_conversas) FROM mart.fct_sessao")[0] \
            == _um("SELECT count(*) FROM stg.conversa WHERE conta_como_uso")[0]
        assert _um("SELECT count(*) FROM mart.fct_sessao WHERE ts_fim < ts_inicio")[0] == 0
        assert _um("SELECT sum(n_sessoes) FROM mart.dim_usuario")[0] == _um("SELECT count(*) FROM mart.fct_sessao")[0]

    def test_nenhum_elegivel_imaturo_ou_burn_in(self):
        assert _um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel AND (NOT maduro OR burn_in OR trafego_anomalo)")[0] == 0
        assert _um("SELECT count(*) FROM mart.dim_usuario WHERE NOT elegivel AND motivo_inelegivel IS NULL")[0] == 0
        assert _um("SELECT count(*) FROM mart.dim_usuario WHERE elegivel AND motivo_inelegivel IS NOT NULL")[0] == 0

    def test_voltou_coerente_com_sessoes(self):
        assert _um(
            "SELECT count(*) FROM mart.fct_primeira_experiencia f WHERE f.voltou_7d <> EXISTS ("
            "SELECT 1 FROM mart.fct_sessao s JOIN mart.fct_sessao s1 ON s1.usuario_id = s.usuario_id AND s1.seq = 1 "
            "WHERE s.usuario_id = f.usuario_id AND s.seq > 1 "
            "AND s.ts_inicio <= s1.ts_inicio + ops.param('janela_retorno_horas')::int * interval '1 hour')")[0] == 0
        assert _um("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE voltou_7d <> (horas_ate_retorno IS NOT NULL)")[0] == 0

    def test_faixas_com_pelo_menos_10_por_cento(self):
        total = _um("SELECT count(*) FROM mart.fct_primeira_experiencia")[0]
        for col in ("faixa_chars_pergunta", "faixa_chars_resposta"):
            for faixa, n in _q(f"SELECT {col}, count(*) FROM mart.fct_primeira_experiencia GROUP BY 1"):
                assert n / total >= 0.10, (col, faixa, n)

    def test_calc_retencao_oficial_igual_aos_marts(self):
        usuarios, voltaram, taxa = _um("SELECT * FROM mart.calc_retencao('oficial')")
        el, vo = _um("SELECT count(*), count(*) FILTER (WHERE voltou_7d) FROM mart.fct_primeira_experiencia WHERE elegivel")
        assert (usuarios, voltaram) == (el, vo)
        assert float(taxa) == pytest.approx(vo / el, abs=1e-6)
        assert 0.15 < vo / el < 0.35  # ordem de 24% (discovery)
