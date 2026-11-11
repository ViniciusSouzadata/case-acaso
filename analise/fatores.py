"""Lista de fatores analisados (REQ-212), seus grupos e o preparo dos níveis (funções puras sobre o DataFrame de dados.py).

Um fator vira uma Series de níveis (texto) alinhada ao DataFrame; linhas fora da população daquele fator ficam nulas
(ex.: idioma divergente só vale para perguntas com mais de 30 caracteres, porque em pergunta curta é sobretudo erro de
detecção: 61% de divergência em até 30 caracteres contra 10% nas mais longas, ver figura 06 e STATE de 11/11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

ASSISTENTE, PERFIL, ENGAJAMENTO = "assistente", "perfil", "engajamento"
FAIXA_PERGUNTA_CURTA = "até 30"  # rótulo de mart.fct_primeira_experiencia.faixa_chars_pergunta
IDIOMAS_PRINCIPAIS = ("Portuguese", "English", "Spanish")  # o resto vira "outros" (muitos são erro de detecção)
RAROS = "outros"


@dataclass(frozen=True)
class Fator:
    nome: str
    grupo: str
    preparar: Callable[[pd.DataFrame], pd.Series]  # devolve nível (texto) por linha; NaN = fora da população do fator


def agrupar_raros(niveis: pd.Series, n_minimo: int) -> pd.Series:
    """Níveis com menos de n_minimo linhas viram "outros" (se sobrar um único nível raro, ele permanece como está)."""
    contagem = niveis.value_counts()
    raros = set(contagem[contagem < n_minimo].index)
    if len(raros) < 2:
        return niveis
    return niveis.where(~niveis.isin(raros), RAROS)


def _texto(s: pd.Series) -> pd.Series:
    return s.astype(object).where(s.notna(), None)


def _sim_nao(s: pd.Series) -> pd.Series:
    return s.map({True: "sim", False: "não"})


def _faixas(s: pd.Series, limites: list[tuple[int, str]], ultimo: str) -> pd.Series:
    def f(v):
        for lim, rot in limites:
            if v <= lim:
                return rot
        return ultimo
    return s.map(f)


def _top_k_mais_demais(niveis: pd.Series, k: int, rotulo: str, excluir: tuple[str, ...] = ()) -> pd.Series:
    """Mantém os k níveis mais frequentes (fora os de `excluir`); o resto vira `rotulo`. Decisão do planejador (limite de ~25
    parâmetros): região = 2 maiores + "outras regiões"; tema = 3 maiores específicos + "demais temas" (inclui indefinido)."""
    contagem = niveis[~niveis.isin(excluir)].value_counts()
    manter = set(sorted(contagem.index, key=lambda x: (-contagem[x], str(x)))[:k])
    return niveis.where(niveis.isin(manter), rotulo).where(niveis.notna())


def _regiao(df: pd.DataFrame) -> pd.Series:
    return _top_k_mais_demais(_texto(df["regiao"]), 2, "outras regiões")


def _tema(df: pd.DataFrame) -> pd.Series:
    t = _texto(df["tema"])
    if not (t.isin(["não classificado"]).all()):
        return _top_k_mais_demais(t, 3, "demais temas", excluir=("outros/indefinido", "não classificado"))
    return t  # sem seed: um só nível, o fator não entra


def _idioma(df: pd.DataFrame) -> pd.Series:
    i = _texto(df["idioma"])
    return i.where(i.isin(IDIOMAS_PRINCIPAIS), RAROS)


def _idioma_divergente(df: pd.DataFrame) -> pd.Series:
    nivel = _sim_nao(df["idioma_divergente"])
    return nivel.where(df["faixa_chars_pergunta"].astype(object) != FAIXA_PERGUNTA_CURTA)


FATORES: list[Fator] = [
    # assistente: o que a resposta do assistente fez
    Fator("recusa", ASSISTENTE, lambda d: _sim_nao(d["recusa"])),
    Fator("idioma_divergente", ASSISTENTE, _idioma_divergente),
    Fator("faixa_chars_resposta", ASSISTENTE, lambda d: _texto(d["faixa_chars_resposta"])),
    Fator("modelo_familia", ASSISTENTE, lambda d: _texto(d["modelo_familia"])),
    # perfil: quem chegou e quando
    Fator("tema", PERFIL, _tema),
    Fator("idioma", PERFIL, _idioma),
    Fator("dispositivo", PERFIL, lambda d: _texto(d["dispositivo"])),
    Fator("periodo_dia", PERFIL, lambda d: _texto(d["periodo_dia"])),
    Fator("fim_de_semana", PERFIL, lambda d: _sim_nao(d["fim_de_semana"])),
    Fator("faixa_chars_pergunta", PERFIL, lambda d: _texto(d["faixa_chars_pergunta"])),
    Fator("regiao", PERFIL, _regiao),
    Fator("era_modelo", PERFIL, lambda d: _texto(d["era_modelo"])),
    # engajamento: consequência da experiência, não causa (descritivo, fora do ajuste)
    Fator("n_turnos_sessao", ENGAJAMENTO,
          lambda d: _faixas(d["n_turnos_sessao"], [(1, "1"), (3, "2 a 3")], "4 ou mais")),
    Fator("n_conversas_sessao", ENGAJAMENTO,
          lambda d: _faixas(d["n_conversas_sessao"], [(1, "1"), (2, "2")], "3 ou mais")),
]
