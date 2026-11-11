"""T-104: unitários de loader/derivar.py (sem banco)."""
from datetime import datetime, timezone

import pytest

from loader import derivar as d

WIN_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WIN_EDGE = WIN_CHROME + " Edg/120.0.0.0"
WIN_OPERA = WIN_CHROME + " OPR/106.0.0.0"
ANDROID_CHROME = "Mozilla/5.0 (Linux; Android 13; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
IPHONE_SAFARI = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
MAC_SAFARI = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
LINUX_FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"


@pytest.mark.parametrize("ua,so", [
    (WIN_CHROME, "windows"), (ANDROID_CHROME, "android"), (IPHONE_SAFARI, "ios"),
    (MAC_SAFARI, "mac"), (LINUX_FIREFOX, "linux"), ("curl/8.0", "outro"), ("", "outro"), (None, "outro"),
])
def test_familia_so(ua, so):
    assert d.familia_so(ua) == so


@pytest.mark.parametrize("ua,nav", [
    (WIN_CHROME, "chrome"), (WIN_EDGE, "edge"), (WIN_OPERA, "opera"), (IPHONE_SAFARI, "safari"),
    (MAC_SAFARI, "safari"), (LINUX_FIREFOX, "firefox"), ("curl/8.0", "outro"), (None, "outro"),
])
def test_familia_navegador(ua, nav):
    assert d.familia_navegador(ua) == nav


def test_edge_e_opera_nao_viram_chrome():
    assert d.familia_navegador(WIN_EDGE) != "chrome"
    assert d.familia_navegador(WIN_OPERA) != "chrome"


@pytest.mark.parametrize("so,disp", [("android", "celular"), ("ios", "celular"), ("windows", "computador"),
                                     ("mac", "computador"), ("linux", "computador"), ("outro", "outro")])
def test_dispositivo(so, disp):
    assert d.familia_dispositivo(so) == disp


def test_ua_desconhecido_vai_para_outro():
    assert (d.familia_so("xyz"), d.familia_navegador("xyz"), d.familia_dispositivo(d.familia_so("xyz"))) == ("outro",) * 3


def test_chaves_usuario():
    k = d.chaves_usuario("ABC", WIN_CHROME, "windows", "chrome")
    assert len(k["usuario_id"]) == 64 and len({*k.values()}) == 3
    # normalização: maiúsculas/bordas não mudam a chave; versão do navegador não entra na oficial
    assert d.chaves_usuario(" abc ", WIN_CHROME, "windows", "chrome")["usuario_id"] == k["usuario_id"]
    k2 = d.chaves_usuario("abc", WIN_CHROME.replace("120", "121"), "windows", "chrome")
    assert k2["usuario_id"] == k["usuario_id"] and k2["usuario_id_ip_ua"] != k["usuario_id_ip_ua"]
    assert d.chaves_usuario("abc", WIN_CHROME, "windows", "firefox")["usuario_id"] != k["usuario_id"]
    assert d.chaves_usuario(None, WIN_CHROME, "windows", "chrome")["usuario_id"] is None


@pytest.mark.parametrize("m,fam", [("gpt-4-0314", "gpt-4"), ("gpt-4-xxxx", "gpt-4"), ("GPT-4-1106-preview", "gpt-4"),
                                   ("gpt-3.5-turbo-0613", "gpt-3.5"), ("outro-modelo", "gpt-3.5"), (None, "gpt-3.5")])
def test_familia_modelo(m, fam):
    assert d.familia_modelo(m) == fam


@pytest.mark.parametrize("p,r,esperado", [
    ("Portuguese", "Portuguese", False), ("Portuguese", "English", True), ("Nolang", "English", False),
    ("Portuguese", "Nolang", False), (None, "English", False), ("English", None, False), ("", "English", False),
])
def test_idioma_divergente(p, r, esperado):
    assert d.idioma_divergente(p, r) is esperado


@pytest.mark.parametrize("estado,fuso", [
    ("Acre", "America/Rio_Branco"), ("Amazonas", "America/Manaus"), ("Roraima", "America/Manaus"),
    ("Rondônia", "America/Manaus"), ("Rondonia", "America/Manaus"), ("Mato Grosso", "America/Manaus"),
    ("Mato Grosso do Sul", "America/Manaus"), ("São Paulo", "America/Sao_Paulo"),
    ("Federal District", "America/Sao_Paulo"), ("Piauí", "America/Sao_Paulo"), ("Amapá", "America/Sao_Paulo"),
    (None, "America/Sao_Paulo"), ("", "America/Sao_Paulo"), ("Narnia", "America/Sao_Paulo"),
])
def test_fuso(estado, fuso):
    assert d.fuso_do_estado(estado) == fuso


def test_vazia_e_tamanho():
    assert d.mensagem_vazia("") and d.mensagem_vazia("  \n\t ") and d.mensagem_vazia(None)
    assert not d.mensagem_vazia(" oi ")
    assert d.tamanho(None) == 0 and d.tamanho("") == 0 and d.tamanho("açaí") == 4


def test_recusa():
    padroes = ["i'm sorry", "não posso"]
    assert d.detectar_recusa("I'M SORRY, but...", padroes)
    assert d.detectar_recusa("Desculpe, eu NÃO POSSO ajudar", padroes)
    assert not d.detectar_recusa("Claro, aqui está a resposta", padroes)
    assert not d.detectar_recusa(None, padroes) and not d.detectar_recusa("", padroes)


def test_conta_como_uso():
    assert d.conta_como_uso(["oi", None], 1)
    assert not d.conta_como_uso(["", "  "], 1)
    assert not d.conta_como_uso([], 1)
    assert not d.conta_como_uso(["oi"], 0)


def test_tema():
    assert d.aplicar_tema(1, {}) == ("não classificado", None)
    assert d.aplicar_tema(None, {1: ("x", "y")}) == ("não classificado", None)
    assert d.aplicar_tema(1, {1: ("programação", "regras")}) == ("programação", "regras")


def test_rejeicao():
    a = datetime(2024, 1, 1, tzinfo=timezone.utc)
    b = datetime(2024, 1, 2, tzinfo=timezone.utc)
    assert d.motivo_rejeicao(None, 1, a, b) == d.MOTIVO_ID_NULO
    assert d.motivo_rejeicao(1, 0, None, b) == d.MOTIVO_SEM_RESPOSTA
    assert d.motivo_rejeicao(1, 1, b, a) == d.MOTIVO_TS_INVERTIDO
    assert d.motivo_rejeicao(1, 1, a, a) is None and d.motivo_rejeicao(1, 1, a, b) is None


def test_derivar_conversa_completa_e_sem_texto():
    a = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bruto = dict(conversa_id=7, conversation_hash="h", hash_repetido=False, hashed_ip="ip", user_agent=IPHONE_SAFARI,
                 accept_language="pt-BR", model="gpt-4-0314", ts_inicio=a, ts_fim=a, turn=2,
                 idioma_conversa="Portuguese", mensagens_usuario=["   ", "oi"], idioma_usuario_1="Portuguese",
                 resposta_1="Sorry? I'm sorry, but no", idioma_resposta_1="English", n_respostas_assistente=1,
                 estado=None, redacted=False, ip_mudou=False)
    r = d.derivar_conversa(bruto, ["i'm sorry"], {})
    assert (r["ua_so"], r["ua_navegador"], r["ua_dispositivo"]) == ("ios", "safari", "celular")
    assert r["pergunta_vazia"] and r["conta_como_uso"] and r["recusa_1"] and r["idioma_divergente"]
    assert r["modelo_familia"] == "gpt-4" and r["fuso"] == "America/Sao_Paulo" and r["chars_pergunta_1"] == 3
    assert not any(isinstance(v, str) and ("Sorry" in v or "oi" == v) for v in r.values())
