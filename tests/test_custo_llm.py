"""scripts/custo_llm.py: agrega o log de chamadas (números medidos) e projeta sem inventar."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import custo_llm as C  # noqa: E402

CAB = ["quando", "modelo", "n_itens", "tokens_entrada", "tokens_saida", "custo_usd", "latencia_s", "status"]


def test_agrega_e_projeta(tmp_path):
    log = tmp_path / "log.csv"
    with log.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(CAB)
        w.writerow(["t", "bedrock:m", 10, 6000, 500, "0.012000", "1.5", "ok"])
        w.writerow(["t", "bedrock:m", 10, 6000, 500, "0.012000", "1.5", "parcial:8/10"])
    saida = tmp_path / "c.md"
    assert C.main([str(log), str(saida)]) == 0
    texto = saida.read_text(encoding="utf-8")
    por = C.agregar(list(csv.DictReader(log.open(encoding="utf-8"))))
    assert por["bedrock:m"]["itens"] == 20 and por["bedrock:m"]["falhas"] == 1
    assert "US$ 0,02" in texto and "US$ 1,20" in texto            # 0,02 medido; 0,0012 por conversa -> US$ 1,20 por 1.000
    assert "US$ 13,85" in texto and "US$ 1.005,60" in texto         # projeções = custo por conversa × tamanho da base
    assert "Alavancas de custo" in texto


def test_sem_log_falha_com_mensagem(tmp_path):
    assert C.main([str(tmp_path / "nada.csv")]) == 1
