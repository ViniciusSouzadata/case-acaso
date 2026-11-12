"""Previsões de cada classificador nas 200 conversas rotuladas (T-205b), em `seeds/validacao_previsoes.csv`.

Serve para `python -m analise validacao` comparar cada classificador com os rótulos do Vinícius NAS 200 COMPLETAS, sem depender do
seed de tema (que passa a ter a rodada do LLM) nem do snapshot (que o compose não monta):
  regras    aplicadas aqui, na hora, ao texto das 200 (tema por `seeds/regras_tema.yaml`, recusa por `seeds/regras_recusa.yaml`);
  LLM       lido do cache da validação (`data/cache_llm/`); só entra o que está no cache (nada é reenviado).
O arquivo tem só conversa_id, classificador, versão e rótulos: nenhum texto de conversa.

Uso:  python -m classificador.previsoes_200 [<id do modelo na OpenRouter>]     (padrão: anthropic/claude-haiku-5.5)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "seeds" / "validacao_previsoes.csv"
CABECALHO = ["conversa_id", "classificador", "versao", "tema", "recusa"]


def gerar(modelo: str = "anthropic/claude-haiku-5.5", saida: Path = SAIDA) -> dict[str, int]:
    sys.path.insert(0, str(RAIZ))
    from analise import validacao as V
    from classificador import openrouter as O
    from classificador.tema import ProvedorRegras, primeira_pergunta
    from loader.derivar import detectar_recusa

    humanos = V.ler_rotulos()
    ids = set(humanos)
    versao_recusa, padroes = V._padroes_recusa()
    regras = ProvedorRegras()
    linhas, achados = [], set()
    for cid, mensagens, resposta in V._conversas_do_bruto(V.SNAPSHOT):
        if cid in ids:
            achados.add(cid)
            linhas.append([cid, "regras", f"{regras.versao}|{versao_recusa}", regras.classificar(primeira_pergunta(mensagens) or ""),
                           "true" if detectar_recusa(resposta, padroes) else "false"])
    if achados != ids:
        raise ValueError(f"{len(ids - achados)} conversas rotuladas não estão no snapshot")
    cache = O.ClassificadorOpenRouter(modelo, lambda *_: ("", O.Uso()), 0.0, 0.0).cache  # só lê o cache; não chama a rede
    origem = f"openrouter:{modelo}"
    faltam = sorted(ids - set(cache))
    if faltam:
        raise ValueError(f"{len(faltam)} das 200 não estão no cache do {modelo}; rode `python -m classificador.validar_llm {modelo}` antes")
    for cid in sorted(ids):
        tema, rec = cache[cid]
        linhas.append([cid, origem, O.PROMPT_VERSAO, tema, "true" if rec else "false"])
    linhas.sort(key=lambda l: (l[1] != "regras", l[0]))
    with saida.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECALHO)
        w.writerows(linhas)
    return {"conversas": len(ids), "linhas": len(linhas)}


if __name__ == "__main__":
    r = gerar(*sys.argv[1:2])
    print(f"{SAIDA}: {r['linhas']} linhas para {r['conversas']} conversas")
