"""Classificação de tema (T-205): interface única `classificar(pergunta) -> tema`, provedores trocáveis por TEMA_PROVEDOR.

Provedores:
  regras     palavras-chave de seeds/regras_tema.yaml, sem LLM. É o PADRÃO (não precisa de credencial nem de rede).
  bedrock    Claude Haiku no Amazon Bedrock (reserva: Amazon Nova). Requer boto3 e credencial AWS no ambiente/.env.
  anthropic  mesmo modelo pela API da Anthropic (provedor alternativo, ADR-09). Requer ANTHROPIC_API_KEY.

Os provedores com LLM recebem só a 1ª pergunta, truncada em TRUNCAR_EM caracteres, e devolvem só um rótulo da taxonomia.
Nada além do rótulo é gravado; texto de conversa nunca é impresso nem registrado. A transmissão ao modelo é injetada
(`chamar`), por isso os testes rodam sem rede.

Uso:  python -m classificador.tema gerar [--provedor regras|bedrock|anthropic] [--saida seeds/tema_conversa.csv]
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Callable, Protocol

import yaml

RAIZ = Path(__file__).resolve().parent.parent
REGRAS_TEMA = RAIZ / "seeds" / "regras_tema.yaml"
SNAPSHOT = RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"
SAIDA_PADRAO = RAIZ / "seeds" / "tema_conversa.csv"

TRUNCAR_EM = 1000
PROMPT_VERSAO = "1.0.0"  # versão do prompt dos provedores com LLM; suba ao mudar o texto de PROMPT_SISTEMA ou a taxonomia

TAXONOMIA = [
    "estudo/dever de casa",
    "programação/TI",
    "escrita e tradução",
    "trabalho/negócios",
    "criação/ficção e roleplay",
    "informação geral/curiosidade",
    "conversa pessoal/conselho",
    "outros/indefinido",
]
INDEFINIDO = "outros/indefinido"

PROMPT_SISTEMA = (
    "Você classifica o assunto da primeira pergunta de um usuário a um assistente de IA. "
    "Escolha exatamente UM tema da lista, sem inventar outro:\n"
    + "\n".join(f"- {t}" for t in TAXONOMIA)
    + '\nResponda somente com JSON na forma {"tema": "<um tema da lista>"}.'
)


class Provedor(Protocol):
    nome: str
    modelo: str | None

    def classificar(self, pergunta: str) -> str: ...


# ----------------------------------------------------------------------------------------------- regras
def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def _padrao(palavra: str) -> re.Pattern:
    inteira = palavra.endswith("$")
    base = _sem_acento(palavra[:-1] if inteira else palavra).lower()
    return re.compile(r"(?<!\w)" + re.escape(base) + (r"(?!\w)" if inteira else ""))


def carregar_regras(caminho: Path = REGRAS_TEMA) -> tuple[str, list[tuple[str, list[re.Pattern]]]]:
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    regras = [(g["tema"], [_padrao(p) for p in g["palavras"]]) for g in dados["temas"]]
    return str(dados["versao"]), regras


class ProvedorRegras:
    nome = "regras"
    modelo = None

    def __init__(self, caminho: Path = REGRAS_TEMA):
        self.versao, self._regras = carregar_regras(caminho)

    @property
    def versao_prompt(self) -> str:
        return self.versao

    def classificar(self, pergunta: str) -> str:
        texto = _sem_acento((pergunta or "")[:TRUNCAR_EM]).lower()
        melhor, melhor_n = INDEFINIDO, 0
        for tema, padroes in self._regras:  # a ordem do YAML desempata (só substitui se tiver MAIS acertos)
            n = sum(1 for p in padroes if p.search(texto))
            if n > melhor_n:
                melhor, melhor_n = tema, n
        return melhor


# ----------------------------------------------------------------------------------------------- LLM
def extrair_tema(resposta: str) -> str | None:
    """Tema válido (da taxonomia) dentro da resposta do modelo, ou None. Aceita JSON puro ou JSON cercado de texto."""
    achado = re.search(r"\{.*?\}", resposta or "", re.S)
    if not achado:
        return None
    try:
        tema = json.loads(achado.group(0)).get("tema")
    except (json.JSONDecodeError, AttributeError):
        return None
    return tema if tema in TAXONOMIA else None


class _ProvedorLLM:
    """Base dos provedores com LLM: trunca, chama, valida a saída, tenta de novo uma vez e cai em 'outros/indefinido'."""
    nome = "llm"
    versao_prompt = PROMPT_VERSAO

    def __init__(self, modelo: str, chamar: Callable[[str, str], str]):
        self.modelo = modelo
        self._chamar = chamar

    def classificar(self, pergunta: str) -> str:
        enviado = (pergunta or "")[:TRUNCAR_EM]
        for _ in range(2):
            tema = extrair_tema(self._chamar(PROMPT_SISTEMA, enviado))
            if tema:
                return tema
        return INDEFINIDO


class ProvedorBedrock(_ProvedorLLM):
    nome = "bedrock"

    def __init__(self, modelo: str, chamar: Callable[[str, str], str] | None = None, regiao: str = "us-east-1"):
        super().__init__(modelo, chamar or self._chamada_real(modelo, regiao))

    @staticmethod
    def _chamada_real(modelo: str, regiao: str) -> Callable[[str, str], str]:
        import boto3  # só aqui: fica fora da imagem do compose (classificador/requirements.txt)

        cliente = boto3.client("bedrock-runtime", region_name=regiao)

        def chamar(sistema: str, pergunta: str) -> str:
            r = cliente.converse(
                modelId=modelo, system=[{"text": sistema}],
                messages=[{"role": "user", "content": [{"text": pergunta}]}],
                inferenceConfig={"maxTokens": 60, "temperature": 0},
            )
            return r["output"]["message"]["content"][0]["text"]
        return chamar


class ProvedorAnthropic(_ProvedorLLM):
    nome = "anthropic"

    def __init__(self, modelo: str, chamar: Callable[[str, str], str] | None = None, chave: str | None = None):
        super().__init__(modelo, chamar or self._chamada_real(modelo, chave or os.environ.get("ANTHROPIC_API_KEY", "")))

    @staticmethod
    def _chamada_real(modelo: str, chave: str) -> Callable[[str, str], str]:
        import urllib.request

        if not chave:
            raise RuntimeError("ANTHROPIC_API_KEY não definida (gravar só em .env, nunca no repositório)")

        def chamar(sistema: str, pergunta: str) -> str:
            corpo = json.dumps({"model": modelo, "max_tokens": 60, "temperature": 0, "system": sistema,
                                "messages": [{"role": "user", "content": pergunta}]}).encode()
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=corpo, headers={
                "x-api-key": chave, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())["content"][0]["text"]
        return chamar


def criar_provedor(nome: str | None = None, env: dict | None = None) -> Provedor:
    """Provedor pela configuração: argumento > TEMA_PROVEDOR > 'regras' (padrão, sem credencial)."""
    env = os.environ if env is None else env
    nome = (nome or env.get("TEMA_PROVEDOR") or "regras").lower()
    if nome == "regras":
        return ProvedorRegras()
    if nome == "bedrock":
        modelo = env.get("TEMA_BEDROCK_MODELO")
        if not modelo:
            raise RuntimeError("TEMA_BEDROCK_MODELO não definido: informe o id do modelo habilitado na conta (Claude Haiku; "
                               "reserva Amazon Nova em TEMA_BEDROCK_MODELO_RESERVA)")
        return ProvedorBedrock(modelo, regiao=env.get("AWS_REGION", "us-east-1"))
    if nome == "anthropic":
        return ProvedorAnthropic(env.get("TEMA_ANTHROPIC_MODELO", "claude-haiku-5-5"), chave=env.get("ANTHROPIC_API_KEY"))
    raise ValueError(f"TEMA_PROVEDOR desconhecido: {nome!r} (use regras, bedrock ou anthropic)")


def classificar(pergunta: str, provedor: Provedor | None = None) -> str:
    """Interface única: tema (da taxonomia) da pergunta. Sem provedor informado, usa a configuração (padrão: regras)."""
    return (provedor or criar_provedor()).classificar(pergunta)


# ----------------------------------------------------------------------------------------------- seed
CABECALHO = ["conversa_id", "tema", "tema_origem", "versao_prompt"]
CONSULTA_PERGUNTAS = """
SELECT conversation[1].turn_identifier AS conversa_id,
       list_transform(list_filter(conversation, lambda t: t.role = 'user'), lambda t: t.content) AS mensagens,
       len(list_filter(conversation, lambda t: t.role = 'assistant')) AS n_respostas
FROM read_parquet(?)
ORDER BY 1
"""


def primeira_pergunta(mensagens: list[str | None]) -> str | None:
    """1ª mensagem de usuário não vazia (a conversa conta como uso se existir alguma)."""
    for m in mensagens or []:
        if m is not None and m.strip():
            return m
    return None


def tema_origem(provedor: Provedor) -> str:
    return f"{provedor.nome}:{provedor.modelo}" if provedor.modelo else f"{provedor.nome}:{provedor.versao_prompt}"


def gerar(provedor: Provedor, snapshot: Path = SNAPSHOT, saida: Path = SAIDA_PADRAO) -> Counter:
    """Classifica a 1ª pergunta de cada conversa que conta como uso e grava o seed. Devolve a contagem por tema."""
    import duckdb

    sys.path.insert(0, str(RAIZ))
    from loader.derivar import conta_como_uso  # mesma regra do loader (fonte única)

    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    cont: Counter = Counter()
    origem = tema_origem(provedor)
    try:
        linhas = con.execute(CONSULTA_PERGUNTAS, [snapshot.as_posix()]).fetchall()
    finally:
        con.close()
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECALHO)
        for conversa_id, mensagens, n_resp in linhas:
            if conversa_id is None or not conta_como_uso(mensagens or [], n_resp or 0):
                continue
            tema = provedor.classificar(primeira_pergunta(mensagens))
            cont[tema] += 1
            w.writerow([conversa_id, tema, origem, provedor.versao_prompt])
    return cont


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "gerar":
        print("uso: python -m classificador.tema gerar [--provedor regras|bedrock|anthropic] [--saida caminho.csv]", file=sys.stderr)
        return 2
    nome = argv[argv.index("--provedor") + 1] if "--provedor" in argv else None
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else SAIDA_PADRAO
    provedor = criar_provedor(nome)
    cont = gerar(provedor, saida=saida)
    total = sum(cont.values())
    print(f"seed gravado em {saida}: {total} conversas, origem {tema_origem(provedor)}, versão {provedor.versao_prompt}")
    for tema, n in cont.most_common():
        print(f"  {tema:<32} {n:>6}  {n / total * 100:5.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
