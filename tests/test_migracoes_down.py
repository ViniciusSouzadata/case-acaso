"""Reversão das migrações: todo `NNN_x.sql` tem seu `NNN_x_down.sql` em sql/migrations_down/ (fora do alcance do executor).
Verificação estrutural (sem banco): a reversão em si é manual e está descrita nos próprios arquivos."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
UP = sorted(p for p in (RAIZ / "sql" / "migrations").glob("*.sql"))
DOWN = RAIZ / "sql" / "migrations_down"


def test_toda_migracao_tem_reversao():
    for p in UP:
        assert (DOWN / f"{p.stem}_down.sql").is_file(), f"falta a reversão de {p.name}"


def test_reversao_em_transacao_e_limpa_o_registro():
    for p in UP:
        t = (DOWN / f"{p.stem}_down.sql").read_text(encoding="utf-8")
        versao = p.name[:3]
        assert re.search(r"^BEGIN;", t, re.M) and re.search(r"^COMMIT;", t, re.M), p.name
        assert f"versao = '{versao}'" in t, p.name


def test_executor_nao_enxerga_as_reversoes():
    from loader import migrar  # noqa: PLC0415 - import tardio: só depende do caminho, não do banco
    assert DOWN not in migrar.PASTA_MIGRACOES.parents and migrar.PASTA_MIGRACOES.name == "migrations"
    assert not any(migrar.PADRAO.match(p.name) for p in (RAIZ / "sql" / "migrations").glob("*_down.sql"))


def test_reversao_nao_apaga_dado_de_tabela_de_outra_migracao():
    # DROP TABLE só de tabelas criadas pela própria migração
    for p in UP:
        up = p.read_text(encoding="utf-8")
        criadas = set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?([\w.]+)", up))
        down = (DOWN / f"{p.stem}_down.sql").read_text(encoding="utf-8")
        for apagada in re.findall(r"DROP TABLE IF EXISTS ([\w.]+)", down):
            assert apagada in criadas, f"{p.name}: a reversão apaga {apagada}, que não é dela"
