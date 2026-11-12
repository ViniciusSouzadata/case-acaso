"""Gera docs/custo_llm.md a partir do log de chamadas (data/cache_llm/chamadas.csv): só números MEDIDOS, nenhum texto de conversa.

Uso:  python scripts/custo_llm.py [log.csv] [saida.md]
Projeções = custo medido por conversa × tamanho da base (sem número inventado): base Brasil inteira e WildChat inteiro (838 mil).
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LOG = RAIZ / "data" / "cache_llm" / "chamadas.csv"
SAIDA = RAIZ / "docs" / "custo_llm.md"
BASE_BRASIL = 11_545       # conversas que contam como uso no snapshot (seeds/tema_conversa.csv)
WILDCHAT_INTEIRO = 838_000  # ordem de grandeza informada pela Acaso/planejador; confira antes de citar


def agregar(linhas: list[dict]) -> dict[str, dict]:
    por: dict[str, dict] = defaultdict(lambda: {"chamadas": 0, "itens": 0, "tok_in": 0, "tok_out": 0, "custo": 0.0, "lat": 0.0, "falhas": 0})
    for l in linhas:
        a = por[l["modelo"]]
        a["chamadas"] += 1
        a["itens"] += int(l["n_itens"])
        a["tok_in"] += int(l["tokens_entrada"])
        a["tok_out"] += int(l["tokens_saida"])
        a["custo"] += float(l["custo_usd"])
        a["lat"] += float(l["latencia_s"])
        a["falhas"] += 0 if l["status"] == "ok" else 1
    return dict(por)


def _usd(x: float) -> str:
    return f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def relatorio(por: dict[str, dict]) -> str:
    cab = ["# Custo do classificador LLM (medido)", "",
           "Gerado por `scripts/custo_llm.py` a partir do log de chamadas (sem texto de conversa). Todos os números vêm do log; "
           "projeções são custo medido por conversa × tamanho da base.", "",
           "| Modelo | Chamadas | Conversas enviadas | Tokens entrada | Tokens saída | Custo medido | Custo por 1.000 conversas | "
           "Base Brasil (11.545) | WildChat inteiro (838 mil) | Chamadas com falha/parcial |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for modelo, a in sorted(por.items()):
        por_conv = a["custo"] / a["itens"] if a["itens"] else 0.0
        cab.append(f"| {modelo} | {a['chamadas']} | {a['itens']} | {a['tok_in']} | {a['tok_out']} | {_usd(a['custo'])} | {_usd(1000 * por_conv)} | "
                   f"{_usd(BASE_BRASIL * por_conv)} | {_usd(WILDCHAT_INTEIRO * por_conv)} | {a['falhas']} |")
    cab += ["", "## Alavancas de custo (o que reduz token sem perder a leitura)",
            "- **Amostra validada antes de escalar:** 200 conversas rotuladas por pessoa decidem o modelo; só depois roda a base.",
            "- **Só a 1ª conversa de cada usuário** que entra em algum número (união das 4 definições), não a base inteira.",
            "- **Truncamento** da pergunta e da resposta (600 caracteres, a mesma régua do humano).",
            "- **Lote** de 10 conversas por chamada (um prompt de instruções para dez itens).",
            "- **Cache:** conversa já classificada (modelo + versão do prompt) nunca é reenviada.",
            "- **Teto** `LLM_TETO_USD` (padrão US$ 3,00): a execução para ao atingir.",
            "- **Modelo barato o bastante** escolhido pelo kappa de tema, com custo como desempate (ver `docs/validacao_llm.md`).", ""]
    return "\n".join(cab)


def main(argv: list[str]) -> int:
    log = Path(argv[0]) if argv else LOG
    saida = Path(argv[1]) if len(argv) > 1 else SAIDA
    if not log.is_file():
        print(f"sem log de chamadas em {log}: rode a validação primeiro (python -m classificador.validar_llm)", file=sys.stderr)
        return 1
    with log.open(encoding="utf-8", newline="") as f:
        por = agregar(list(csv.DictReader(f)))
    saida.write_text(relatorio(por), encoding="utf-8")
    print(f"custo_llm.md gravado: {len(por)} modelo(s), gasto medido total {_usd(sum(a['custo'] for a in por.values()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
