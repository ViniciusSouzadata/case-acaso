"""Fabrica da base sintetica de resposta conhecida (T-105).

`gerar(caminho_parquet)` escreve um parquet com o MESMO esquema do bruto real
(data/bruto/wildchat_brasil.parquet). Todos os textos sao inventados e inofensivos.
A resposta esperada de cada caso esta em tests/esperado.py.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

try:
    from tests.esperado import ip
except ImportError:  # pytest com tests/ no sys.path (sem __init__.py)
    from esperado import ip

UTC = timezone.utc
TS = pa.timestamp("us", tz="UTC")

_CATEGORIAS = [
    "harassment", "harassment/threatening", "harassment_threatening", "hate",
    "hate/threatening", "hate_threatening", "self-harm", "self-harm/instructions",
    "self-harm/intent", "self_harm", "self_harm_instructions", "self_harm_intent",
    "sexual", "sexual/minors", "sexual_minors", "violence", "violence/graphic",
    "violence_graphic",
]
_DETOXIFY = ["identity_attack", "insult", "obscene", "severe_toxicity",
             "sexual_explicit", "threat", "toxicity"]

_HEADER = pa.struct([("accept-language", pa.string()), ("user-agent", pa.string())])
_TURNO = pa.struct([
    ("content", pa.string()), ("country", pa.string()), ("hashed_ip", pa.string()),
    ("header", _HEADER), ("language", pa.string()), ("redacted", pa.bool_()),
    ("role", pa.string()), ("state", pa.string()), ("timestamp", TS),
    ("toxic", pa.bool_()), ("turn_identifier", pa.int64()),
])
_OPENAI = pa.struct([
    ("categories", pa.struct([(c, pa.bool_()) for c in _CATEGORIAS])),
    ("category_scores", pa.struct([(c, pa.float64()) for c in _CATEGORIAS])),
    ("flagged", pa.bool_()),
])
_DETOX = pa.struct([(c, pa.float64()) for c in _DETOXIFY])

ESQUEMA = pa.schema([
    ("conversation_hash", pa.string()),
    ("model", pa.string()),
    ("timestamp", TS),
    ("conversation", pa.list_(_TURNO)),
    ("turn", pa.int64()),
    ("language", pa.string()),
    ("openai_moderation", pa.list_(_OPENAI)),
    ("detoxify_moderation", pa.list_(_DETOX)),
    ("toxic", pa.bool_()),
    ("redacted", pa.bool_()),
    ("state", pa.string()),
    ("country", pa.string()),
    ("hashed_ip", pa.string()),
    ("header", _HEADER),
])

# --- User-agents (familia = SO + navegador; a versao varia) -----------------------
_W = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
_M = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
_L = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
UA = {
    "win_chrome_120": _W + "Chrome/120.0.0.0 Safari/537.36",
    "win_chrome_121": _W + "Chrome/121.0.0.0 Safari/537.36",
    "win_edge": _W + "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "win_firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "win_opera": _W + "Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "mac_chrome": _M + "Chrome/120.0.0.0 Safari/537.36",
    "mac_safari": _M + "Version/17.2 Safari/605.1.15",
    "mac_firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "linux_chrome": _L + "Chrome/120.0.0.0 Safari/537.36",
    "linux_firefox": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "android_chrome": "Mozilla/5.0 (Linux; Android 13; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "android_firefox": "Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
    "ios_safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
}
# 12 familias distintas para o caso E
UAS_CASO_E = ["win_chrome_120", "win_edge", "win_firefox", "win_opera", "mac_chrome",
              "mac_safari", "mac_firefox", "linux_chrome", "linux_firefox",
              "android_chrome", "android_firefox", "ios_safari"]


def _dt(texto: str) -> datetime:
    """'2024-02-01 10:00' -> datetime UTC."""
    return datetime.strptime(texto, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


class _Fabrica:
    def __init__(self) -> None:
        self.linhas: list[dict] = []
        self._turno = 100000

    def _novo_id(self) -> int:
        self._turno += 1
        return self._turno

    def conversa(self, nome_ip: str, ua: str, inicio: datetime, dur_min: int = 5,
                 pergunta: str = "Explique de forma simples como funciona a fotossintese.",
                 sem_assistente: bool = False, hash_conteudo: str | None = None,
                 model: str = "gpt-3.5-turbo-0613") -> None:
        """Uma conversa de 2 pares user/assistant. inicio = 1a resposta; fim = ultima."""
        hip = ip(nome_ip)
        header = {"accept-language": "pt-BR,pt;q=0.9", "user-agent": ua}
        fim = inicio + timedelta(minutes=dur_min)

        def user(texto: str) -> dict:
            return {"content": texto, "country": "Brazil", "hashed_ip": hip,
                    "header": header, "language": "Portuguese", "redacted": False,
                    "role": "user", "state": "Sao Paulo", "timestamp": None,
                    "toxic": False, "turn_identifier": self._novo_id()}

        def assistente(ts: datetime) -> dict:
            return {"content": "Resposta sintetica de teste.", "country": None,
                    "hashed_ip": None, "header": None, "language": "Portuguese",
                    "redacted": False, "role": "assistant", "state": None,
                    "timestamp": ts, "toxic": False, "turn_identifier": self._novo_id()}

        vazia = pergunta == ""
        if sem_assistente:
            turnos = [user(pergunta)]
            ts_topo = inicio  # sem resposta: so existe o horario da conversa
        else:
            turnos = [user(pergunta), assistente(inicio),
                      user("" if vazia else "Obrigado, ficou claro."), assistente(fim)]
            ts_topo = fim
        n = len(self.linhas)
        self.linhas.append({
            "conversation_hash": hash_conteudo or hashlib.md5(f"conv-{n}".encode()).hexdigest(),
            "model": model, "timestamp": ts_topo, "conversation": turnos,
            "turn": len(turnos) // 2, "language": "Portuguese",
            "openai_moderation": [], "detoxify_moderation": [],
            "toxic": False, "redacted": False, "state": "Sao Paulo", "country": "Brazil",
            "hashed_ip": hip, "header": header,
        })


# (nome, 1a conversa, retorno opcional)  -- ver esperado.py para o raciocinio
FILLERS = [
    ("f01", "2024-01-01 12:00", None), ("f02", "2024-01-03 09:00", None),
    ("f03", "2024-01-08 15:00", None), ("f04", "2024-01-12 18:00", None),
    ("f05", "2024-01-20 10:00", None), ("f06", "2024-01-25 10:00", "2024-01-27 10:00"),
    ("f07", "2024-01-30 10:00", None), ("f08", "2024-02-05 16:00", None),
    ("f09", "2024-02-20 11:00", "2024-02-22 11:00"), ("f10", "2024-02-25 20:00", None),
    ("f11", "2024-03-01 08:00", None), ("f12", "2024-03-05 13:00", "2024-03-07 13:00"),
    ("f13", "2024-03-08 14:00", None), ("f14", "2024-03-12 17:00", None),
    ("f15", "2024-03-16 09:30", None), ("f16", "2024-03-20 22:00", None),
    ("f17", "2024-03-26 10:00", None), ("f18", "2024-03-29 12:00", None),
    ("f19", "2024-03-30 15:00", None), ("f20", "2024-03-31 23:00", None),
]
_UAS_FILLER = ["win_chrome_120", "android_chrome", "mac_safari", "win_firefox", "ios_safari"]
_HASH_REPETIDO = hashlib.md5(b"hash-repetido-J-f05").hexdigest()


def montar() -> list[dict]:
    f = _Fabrica()
    # Enchimento: define menor inicio (f01, 2024-01-01 12:00) e maior fim (f20, 23:50)
    for i, (nome, ini, ret) in enumerate(FILLERS):
        ua = UA[_UAS_FILLER[i % len(_UAS_FILLER)]]
        dur = 50 if nome == "f20" else 5
        # f05 compartilha o conversation_hash com J (hash repetido, conversa_id distinto)
        f.conversa(nome, ua, _dt(ini), dur,
                   hash_conteudo=_HASH_REPETIDO if nome == "f05" else None)
        if ret:
            f.conversa(nome, ua, _dt(ret), 5)

    # A: retorno em 6d23h (inicio 02-01 10:00 -> 02-08 09:00)
    f.conversa("A", UA["win_chrome_120"], _dt("2024-02-01 10:00"))
    f.conversa("A", UA["win_chrome_120"], _dt("2024-02-08 09:00"))
    # B: retorno em 7d+1min (02-02 10:00 -> 02-09 10:01)
    f.conversa("B", UA["win_chrome_120"], _dt("2024-02-02 10:00"))
    f.conversa("B", UA["win_chrome_120"], _dt("2024-02-09 10:01"))
    # C: 1a termina 10:10; 2a comeca 10:30 (20 min depois do FIM)
    f.conversa("C", UA["win_chrome_120"], _dt("2024-02-03 10:00"), dur_min=10)
    f.conversa("C", UA["win_chrome_120"], _dt("2024-02-03 10:30"))
    # D: Chrome 120 -> Chrome 121 (mesmo SO/navegador), 3 dias depois
    f.conversa("D", UA["win_chrome_120"], _dt("2024-02-04 14:00"))
    f.conversa("D", UA["win_chrome_121"], _dt("2024-02-07 14:00"))
    # E: 12 user-agents de familias distintas no mesmo IP
    for i, chave in enumerate(UAS_CASO_E):
        f.conversa("E", UA[chave], _dt("2024-02-20 08:00") + timedelta(hours=i))
    # F: so pergunta vazia
    f.conversa("F", UA["win_chrome_120"], _dt("2024-02-10 11:00"), pergunta="")
    # F2: conversa normal e, 3 dias depois, conversa vazia
    f.conversa("F2", UA["mac_safari"], _dt("2024-02-11 11:00"))
    f.conversa("F2", UA["mac_safari"], _dt("2024-02-14 11:00"), pergunta="")
    # G: 1a sessao nos ultimos 7 dias da base (maduro so ate 03-24 23:50)
    f.conversa("G", UA["win_chrome_120"], _dt("2024-03-28 10:00"))
    # H: 1a sessao nos primeiros 14 dias (antes de 01-15 12:00)
    f.conversa("H", UA["win_chrome_120"], _dt("2024-01-05 10:00"))
    # I: sem turno do assistente (rejeitada)
    f.conversa("I", UA["win_chrome_120"], _dt("2024-02-10 10:00"), sem_assistente=True)
    # J: controle (hash repetido com f05)
    f.conversa("J", UA["win_chrome_120"], _dt("2024-02-12 10:00"),
               hash_conteudo=_HASH_REPETIDO)
    # K: mesmo IP, duas familias; conversas separadas por 2 dias
    f.conversa("K", UA["android_chrome"], _dt("2024-02-14 10:00"))
    f.conversa("K", UA["win_firefox"], _dt("2024-02-16 10:00"))
    return f.linhas


def gerar(caminho_parquet: str | Path) -> Path:
    caminho = Path(caminho_parquet)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela = pa.Table.from_pylist(montar(), schema=ESQUEMA)
    pq.write_table(tabela, caminho)
    return caminho


if __name__ == "__main__":
    import sys
    print(gerar(sys.argv[1] if len(sys.argv) > 1 else "data/interim/sintetico.parquet"))
