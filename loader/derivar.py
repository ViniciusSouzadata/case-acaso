"""Derivação das variáveis de texto (T-104): funções puras, sem banco e sem I/O de dados.

Recebem valores simples (str/None/listas) e devolvem valores simples. O texto das conversas
entra aqui só para virar tamanho/flag; nada daqui é gravado como texto.
"""
from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime
from typing import Any

# ---- Chaves de usuário: separador e normalização em UM lugar ------------------------------
SEPARADOR_CHAVE = "|"
TEMA_PADRAO = "não classificado"
SEM_LINGUA = "Nolang"


def _normalizar(parte: str | None) -> str:
    return (parte or "").strip().lower()


def hash_chave(*partes: str | None) -> str:
    """sha256 das partes normalizadas (minúsculas, sem bordas) unidas por SEPARADOR_CHAVE."""
    texto = SEPARADOR_CHAVE.join(_normalizar(p) for p in partes)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def chaves_usuario(hashed_ip: str | None, user_agent: str | None, ua_so: str, ua_navegador: str) -> dict[str, str | None]:
    """usuario_id (oficial: ip|so|navegador), usuario_id_ip e usuario_id_ip_ua. Sem hashed_ip, tudo None."""
    if not _normalizar(hashed_ip):
        return {"usuario_id": None, "usuario_id_ip": None, "usuario_id_ip_ua": None}
    return {
        "usuario_id": hash_chave(hashed_ip, ua_so, ua_navegador),
        "usuario_id_ip": hash_chave(hashed_ip),
        "usuario_id_ip_ua": hash_chave(hashed_ip, user_agent),
    }


# ---- Família de user-agent ----------------------------------------------------------------
def familia_so(ua: str | None) -> str:
    """android/ios/windows/mac/linux/outro. Android e iPhone antes de Linux/Mac (os UAs deles citam ambos)."""
    u = (ua or "").lower()
    if "android" in u:
        return "android"
    if "iphone" in u or "ipad" in u:
        return "ios"
    if "windows" in u:
        return "windows"
    if "mac os" in u:
        return "mac"
    if "linux" in u:
        return "linux"
    return "outro"


def familia_navegador(ua: str | None) -> str:
    """edge/opera/chrome/firefox/safari/outro. Ordem importa: Edg/ e OPR/ trazem 'Chrome/'; Chrome traz 'Safari/'."""
    u = ua or ""
    if "Edg/" in u:
        return "edge"
    if "OPR/" in u:
        return "opera"
    if "Chrome/" in u:
        return "chrome"
    if "Firefox/" in u:
        return "firefox"
    if "Safari/" in u:
        return "safari"
    return "outro"


def familia_dispositivo(ua_so: str) -> str:
    """celular (android/ios), computador (windows/mac/linux), outro."""
    if ua_so in ("android", "ios"):
        return "celular"
    if ua_so in ("windows", "mac", "linux"):
        return "computador"
    return "outro"


# ---- Modelo, idioma, fuso -----------------------------------------------------------------
def familia_modelo(model: str | None) -> str:
    return "gpt-4" if (model or "").lower().startswith("gpt-4") else "gpt-3.5"


def idioma_divergente(idioma_pergunta: str | None, idioma_resposta: str | None) -> bool:
    """Os dois existem, nenhum é Nolang e são diferentes."""
    if not idioma_pergunta or not idioma_resposta:
        return False
    if SEM_LINGUA in (idioma_pergunta, idioma_resposta):
        return False
    return idioma_pergunta != idioma_resposta


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


_FUSO_PADRAO = "America/Sao_Paulo"
_FUSO_POR_ESTADO = {
    "acre": "America/Rio_Branco",
    "amazonas": "America/Manaus",
    "roraima": "America/Manaus",
    "rondonia": "America/Manaus",
    "mato grosso": "America/Manaus",
    "mato grosso do sul": "America/Manaus",
}


def fuso_do_estado(estado: str | None) -> str:
    """Compara sem acento e sem diferença de caixa; nulo ou estado desconhecido -> America/Sao_Paulo."""
    if not estado:
        return _FUSO_PADRAO
    return _FUSO_POR_ESTADO.get(_sem_acento(estado).strip().lower(), _FUSO_PADRAO)


# ---- Texto: só tamanho e flags ------------------------------------------------------------
def tamanho(texto: str | None) -> int:
    return len(texto) if texto else 0


def mensagem_vazia(texto: str | None) -> bool:
    return texto is None or texto.strip() == ""


def detectar_recusa(texto: str | None, padroes: list[str]) -> bool:
    """Algum padrão (já em minúsculas) aparece na resposta em minúsculas."""
    if not texto:
        return False
    t = texto.lower()
    return any(p in t for p in padroes)


def conta_como_uso(mensagens_usuario: list[str | None], n_respostas_assistente: int) -> bool:
    """>= 1 mensagem de usuário não vazia E >= 1 resposta do assistente."""
    return n_respostas_assistente >= 1 and any(not mensagem_vazia(m) for m in mensagens_usuario)


def aplicar_tema(conversa_id: int | None, seed: dict[int, tuple[str, str | None]]) -> tuple[str, str | None]:
    """(tema, tema_origem) do seed; sem entrada -> ('não classificado', None)."""
    if conversa_id is not None and conversa_id in seed:
        return seed[conversa_id]
    return TEMA_PADRAO, None


# ---- Rejeição -----------------------------------------------------------------------------
MOTIVO_ID_NULO = "conversa_id_nulo"
MOTIVO_SEM_RESPOSTA = "sem_resposta_assistente"
MOTIVO_TS_INVERTIDO = "ts_inicio_maior_que_ts_fim"
MOTIVO_ID_DUPLICADO = "conversa_id_duplicado"


def motivo_rejeicao(conversa_id: int | None, n_respostas_assistente: int,
                    ts_inicio: datetime | None, ts_fim: datetime | None) -> str | None:
    """Primeiro motivo que se aplica, ou None. Resposta sem timestamp conta como 'sem resposta'."""
    if conversa_id is None:
        return MOTIVO_ID_NULO
    if n_respostas_assistente < 1 or ts_inicio is None:
        return MOTIVO_SEM_RESPOSTA
    if ts_fim is not None and ts_inicio > ts_fim:
        return MOTIVO_TS_INVERTIDO
    return None


# ---- Registro completo --------------------------------------------------------------------
def derivar_conversa(bruto: dict[str, Any], padroes_recusa: list[str],
                     tema_seed: dict[int, tuple[str, str | None]]) -> dict[str, Any]:
    """Uma linha de stg.conversa (sem lote_id) a partir dos campos brutos de UMA conversa.

    Chaves esperadas em `bruto` (ver carregar.CONSULTA): conversa_id, conversation_hash, hash_repetido,
    hashed_ip, user_agent, accept_language, model, ts_inicio, ts_fim, turn, idioma_conversa,
    mensagens_usuario (lista de str|None), idioma_usuario_1, resposta_1 (str|None), idioma_resposta_1,
    n_respostas_assistente, estado, redacted, ip_mudou.
    """
    so = familia_so(bruto["user_agent"])
    nav = familia_navegador(bruto["user_agent"])
    msgs = bruto["mensagens_usuario"]
    pergunta_1 = msgs[0] if msgs else None
    tema, origem = aplicar_tema(bruto["conversa_id"], tema_seed)
    return {
        "conversa_id": bruto["conversa_id"],
        "conversation_hash": bruto["conversation_hash"],
        "hash_repetido": bool(bruto["hash_repetido"]),
        "hashed_ip": bruto["hashed_ip"],
        "user_agent": bruto["user_agent"],
        "accept_language": bruto["accept_language"],
        "ua_so": so,
        "ua_navegador": nav,
        "ua_dispositivo": familia_dispositivo(so),
        **chaves_usuario(bruto["hashed_ip"], bruto["user_agent"], so, nav),
        "modelo_versao": bruto["model"],
        "modelo_familia": familia_modelo(bruto["model"]),
        "ts_inicio": bruto["ts_inicio"],
        "ts_fim": bruto["ts_fim"],
        "n_turnos": bruto["turn"],
        "idioma_conversa": bruto["idioma_conversa"],
        "idioma_pergunta_1": bruto["idioma_usuario_1"],
        "idioma_resposta_1": bruto["idioma_resposta_1"],
        "idioma_divergente": idioma_divergente(bruto["idioma_usuario_1"], bruto["idioma_resposta_1"]),
        "estado": bruto["estado"],
        "fuso": fuso_do_estado(bruto["estado"]),
        "chars_pergunta_1": tamanho(pergunta_1),
        "chars_resposta_1": tamanho(bruto["resposta_1"]),
        "recusa_1": detectar_recusa(bruto["resposta_1"], padroes_recusa),
        "pergunta_vazia": mensagem_vazia(pergunta_1),
        "conta_como_uso": conta_como_uso(msgs, bruto["n_respostas_assistente"]),
        "ip_mudou": bool(bruto["ip_mudou"]),
        "redacted": bruto["redacted"],
        "tema": tema,
        "tema_origem": origem,
    }
