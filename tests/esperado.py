"""Verdade conhecida da base sintetica (T-105). Escrito A MAO, sem rodar codigo de producao.

Janela fictica (UTC): 2024-01-01 a 2024-03-31 (~90 dias).
  - menor inicio da base : 2024-01-01 12:00  (filler f01)
  - maior fim da base    : 2024-03-31 23:50  (filler f20)
  - burn-in  : inicio da 1a sessao <  2024-01-15 12:00   (menor inicio + 14 d)
  - maduro   : inicio da 1a sessao + 168 h <= 2024-03-31 23:50
               <=> inicio da 1a sessao <= 2024-03-24 23:50
Regras (design.md): sessao = gap <= 30 min entre FIM de uma conversa e INICIO da
seguinte; inicio = 1a resposta do assistente; fim = timestamp de topo;
retorno = outra sessao com inicio <= 168 h apos o inicio da 1a sessao.
Usuario oficial = (hashed_ip, familia SO, familia navegador), sem versao.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


def ip(nome: str) -> str:
    """hashed_ip sintetico e deterministico (64 hex) a partir de um nome."""
    return hashlib.sha256(f"ip-sintetico:{nome}".encode()).hexdigest()


# Parametros de definicao usados no raciocinio abaixo (ops.parametros v1.0.0)
GAP_SESSAO_MIN = 30
JANELA_RETORNO_H = 168
BURN_IN_DIAS = 14
LIMIAR_UAS_IP = 10
MENOR_INICIO = "2024-01-01T12:00:00Z"
MAIOR_FIM = "2024-03-31T23:50:00Z"


@dataclass(frozen=True)
class Caso:
    codigo: str
    descricao: str
    hashed_ips: tuple[str, ...]
    n_conversas: int                 # conversas geradas para o caso
    usuarios_oficiais: int           # usuarios na chave oficial que existem na dim_usuario
    usuarios_so_ip: int              # usuarios pela chave "so IP"
    sessoes: int                     # total de sessoes (soma dos usuarios do caso)
    voltou_7d: bool | None           # vale para todos os usuarios do caso; None = sem usuario
    elegivel: bool | None            # None = o caso nao gera usuario na dim_usuario
    motivo_inelegivel: str | None    # 'trafego_anomalo' | 'imaturo' | 'burn_in' | None
    conta_como_uso: bool             # as conversas do caso contam como uso?
    rejeitada: bool                  # conversa rejeitada na carga?
    n_rejeitadas: int = 0
    n_nao_uso: int = 0               # conversas carregadas que NAO contam como uso


CASOS: dict[str, Caso] = {c.codigo: c for c in [
    Caso("A", "retorno em 6d23h apos o inicio da 1a sessao (conta)", (ip("A"),),
         2, 1, 1, 2, True, True, None, True, False),
    Caso("B", "retorno em 7d + 1 min (nao conta)", (ip("B"),),
         2, 1, 1, 2, False, True, None, True, False),
    Caso("C", "2a conversa 20 min apos o FIM da 1a: mesma sessao, nao e retorno", (ip("C"),),
         2, 1, 1, 1, False, True, None, True, False),
    Caso("D", "mesma pessoa, versao nova do navegador: MESMO usuario; retorno em 3 d", (ip("D"),),
         2, 1, 1, 2, True, True, None, True, False),
    Caso("E", "1 IP com 12 user-agents (12 familias distintas): trafego anomalo", (ip("E"),),
         12, 12, 1, 12, False, False, "trafego_anomalo", True, False),
    Caso("F", "so pergunta vazia: nao conta como uso, sem usuario na dim", (ip("F"),),
         1, 0, 0, 0, None, None, None, False, False, n_nao_uso=1),
    Caso("F2", "conversa normal + pergunta vazia 3 d depois: vazia nao e retorno", (ip("F2"),),
         2, 1, 1, 1, False, True, None, False, False, n_nao_uso=1),
    Caso("G", "1a sessao em 2024-03-28 (ultimos 7 dias): imaturo", (ip("G"),),
         1, 1, 1, 1, False, False, "imaturo", True, False),
    Caso("H", "1a sessao em 2024-01-05 (primeiros 14 dias): burn-in", (ip("H"),),
         1, 1, 1, 1, False, False, "burn_in", True, False),
    Caso("I", "conversa sem turno do assistente: rejeitada na carga", (ip("I"),),
         1, 0, 0, 0, None, None, None, False, True, n_rejeitadas=1),
    Caso("J", "controle: 1 conversa, madura, fora do burn-in", (ip("J"),),
         1, 1, 1, 1, False, True, None, True, False),
    Caso("K", "2 usuarios no mesmo IP (Android/Chrome e Windows/Firefox), conversas a 2 d",
         (ip("K"),), 2, 2, 1, 2, False, True, None, True, False),
]}

# Fillers: f01..f20, um IP cada (ip("f01")...). Ver fabrica_bruto.FILLERS.
#  f01-f04 : 1a sessao entre 01-01 e 01-12  -> burn-in (4)
#  f05-f16 : 1a sessao entre 01-20 e 03-20  -> elegiveis (12); f06, f09, f12 voltam em 2 d
#  f17-f20 : 1a sessao entre 03-26 e 03-31  -> imaturos (4)
FILLER_IPS = tuple(ip(f"f{i:02d}") for i in range(1, 21))
FILLER_CONVERSAS = 23            # 20 primeiras + 3 de retorno
FILLER_USUARIOS = 20
FILLER_ELEGIVEIS = 12
FILLER_RETORNOS = 3              # f06, f09, f12 (entre elegiveis)
FILLER_BURN_IN = 4
FILLER_IMATUROS = 4

# Hash de conversa repetido (conversation_hash nao e unico): J e f05 compartilham o hash.
CONVERSAS_COM_HASH_REPETIDO = 2

# --- Totais, calculados a mao ---------------------------------------------------
# Conversas geradas: fillers 23 + A2 + B2 + C2 + D2 + E12 + F1 + F2(2) + G1 + H1 + I1 + J1 + K2
#   = 23+2+2+2+2 = 31; +12 = 43; +1 = 44; +2 = 46; +1+1+1+1 = 50; +2 = 52
CONVERSAS_GERADAS = 52
# Rejeitadas: so a do caso I (sem resposta do assistente)
CONVERSAS_REJEITADAS = 1
CONVERSAS_CARREGADAS = 51
# Nao contam como uso: F (1) e a 2a de F2 (1)
CONVERSAS_NAO_USO = 2
# Sessoes (so conversas que contam): 52 - 1 rejeitada - 2 nao-uso = 49 conversas validas;
#   fundidas pela regra de 30 min: C (2->1) => 48 sessoes
SESSOES = 48
# Usuarios oficiais (>=1 sessao): fillers 20 + A,B,C,D (4) + E 12 + F2 1 + G,H,J (3) + K 2 = 42
USUARIOS_OFICIAIS = 42
# Pela chave so-IP: K colapsa 2 -> 1 e E colapsa 12 -> 1: 42 - 1 - 11 = 30
USUARIOS_SO_IP = 30
# Elegiveis (maduros, fora do burn-in, sem anomalia): fillers 12 + A,B,C,D (4) + F2 1 + J 1 + K 2 = 20
#   fora: E (12, anomalo), G (imaturo), H (burn-in), fillers burn-in 4 + imaturos 4 -> 22 inelegiveis
USUARIOS_ELEGIVEIS = 20
USUARIOS_INELEGIVEIS = 22
# Retornos entre elegiveis: fillers 3 + A + D = 5 (B nao, C nao, F2 nao, J nao, K nao)
RETORNOS_ENTRE_ELEGIVEIS = 5
# IPs distintos: 20 fillers + 12 casos (A,B,C,D,E,F,F2,G,H,I,J,K) = 32 (a rejeitada I tambem tem IP)
IPS_DISTINTOS = 32
