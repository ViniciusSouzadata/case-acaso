"""T-202: EDA enxuta (no máximo 6 figuras, cada uma com uma conclusão escrita) e resultado.problema_qualidade.

Só agregados: nenhuma figura ou texto mostra conversa, IP ou user-agent. As conclusões saem de números calculados aqui
(nunca digitados); a figura de tema só nasce quando existe mais de um tema no seed (T-205).

Uso:  python -m analise eda
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import psycopg  # noqa: E402

from analise.gravar import substituir  # noqa: E402
from analise.intervalos import wilson  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FIGURAS = Path(os.environ.get("FIGURAS_DIR", RAIZ / "docs" / "figuras"))
MAX_FIGURAS = 6

# Limiar de DIAGNÓSTICO (não é definição de métrica, por isso fora de ops.parametros): semana "anômala" = volume abaixo
# desta fração da mediana das semanas vizinhas (até 4 antes e 4 depois). A 1ª e a última semana da base são parciais e ficam fora.
FRACAO_SEMANA_ANOMALA = 0.5

# Identidade do painel (app/app/globals.css): violeta = série principal, laranja = destaque, cinza = amostra pequena.
COR = "#6a48eb"
COR_CLARA = "#978df8"
COR_DESTAQUE = "#ff6c0e"
COR_CINZA = "#8a8f98"
COR_TINTA = "#121212"
COR_GRADE = "#e6e7ec"
COR_FAIXAS = ["#f1eefe", "#f6f7f9", "#f1eefe", "#f6f7f9"]  # eras de modelo: tons bem claros, alternados
TAMANHO = (5, 3.75)  # 4:3; impressa com ~55 mm de largura no PDF, por isso a letra é grande
FONTE = 12

NOMES_IDIOMA = {
    "Portuguese": "Português", "English": "Inglês", "Spanish": "Espanhol", "French": "Francês", "German": "Alemão",
    "Italian": "Italiano", "Russian": "Russo", "Chinese": "Chinês", "Japanese": "Japonês", "Korean": "Coreano",
    "Arabic": "Árabe", "Finnish": "Finlandês", "Swedish": "Sueco", "Hindi": "Hindi", "Indonesian": "Indonésio", "Ukrainian": "Ucraniano", "Hebrew": "Hebraico", "Vietnamese": "Vietnamita", "Greek": "Grego", "Turkish": "Turco", "Dutch": "Holandês", "Polish": "Polonês", "Latin": "Latim",
}


def _estilo() -> None:
    """Visual do painel: fundo branco, só eixo de baixo e da esquerda em cinza-claro, grade horizontal fina, letra grande."""
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.family": "sans-serif", "font.size": FONTE, "text.color": COR_TINTA,
        "axes.edgecolor": COR_GRADE, "axes.linewidth": 1.0, "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelcolor": COR_CINZA, "axes.labelsize": FONTE, "axes.titlesize": FONTE, "axes.grid": True, "axes.grid.axis": "y",
        "axes.axisbelow": True, "grid.color": COR_GRADE, "grid.linewidth": 0.8,
        "xtick.color": COR_CINZA, "ytick.color": COR_CINZA, "xtick.labelsize": FONTE - 1, "ytick.labelsize": FONTE - 1,
        "xtick.major.size": 0, "ytick.major.size": 0, "legend.fontsize": FONTE - 2, "legend.frameon": False,
    })


def _nome_idioma(x: str) -> str:
    return NOMES_IDIOMA.get(x, x)


def _pct(x: float, casas: int = 1) -> str:
    return f"{x * 100:.{casas}f}%".replace(".", ",")


def _fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


# ----------------------------------------------------------------------------------------------- regras puras
def semanas_anomalas(volumes: list[int], fracao: float = FRACAO_SEMANA_ANOMALA, vizinhas: int = 4) -> list[int]:
    """Posições (0-based) com volume < fracao × mediana das vizinhas. Primeira e última posição não são avaliadas."""
    achadas = []
    for i in range(1, len(volumes) - 1):
        viz = volumes[max(0, i - vizinhas):i] + volumes[i + 1:i + 1 + vizinhas]
        if viz and volumes[i] < fracao * float(np.median(viz)):
            achadas.append(i)
    return achadas


def participacao_topo(contagens: list[int], k: int) -> float:
    """Fatia das conversas que vem dos k maiores (ordenados por volume)."""
    ordenadas = sorted(contagens, reverse=True)
    return sum(ordenadas[:k]) / sum(ordenadas)


# ----------------------------------------------------------------------------------------------- consultas
def _consultar(conn: psycopg.Connection, sql: str, *args) -> list[tuple]:
    return conn.execute(sql, args or None).fetchall()


def _volume_semanal(conn):
    return _consultar(conn, """
        SELECT date_trunc('week', ts_inicio AT TIME ZONE ops.param('fuso_pais'))::date AS semana, count(*)
        FROM stg.conversa GROUP BY 1 ORDER BY 1""")


def _eras(conn):
    return _consultar(conn, "SELECT era, inicio, fim FROM mart.dim_era_modelo ORDER BY inicio")


# ----------------------------------------------------------------------------------------------- figuras
def _salvar(fig, nome: str) -> str:
    PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PASTA_FIGURAS / nome, dpi=240)
    plt.close(fig)
    return nome


def fig_volume(conn) -> tuple[str, str]:
    dados = _volume_semanal(conn)
    semanas = [d[0] for d in dados]
    vol = [int(d[1]) for d in dados]
    anom = semanas_anomalas(vol)
    fig, ax = plt.subplots(figsize=TAMANHO, layout="constrained")
    fim_base = semanas[-1]
    for (_era, ini, fim), cor in zip(_eras(conn), COR_FAIXAS):
        ax.axvspan(ini, fim or fim_base, color=cor, lw=0)
    ax.plot(semanas, vol, color=COR, lw=2.2)
    ax.scatter([semanas[i] for i in anom], [vol[i] for i in anom], color=COR_DESTAQUE, s=40, zorder=3, label="queda forte")
    ax.set_ylim(0, max(vol) * 1.05)
    ax.set_ylabel("conversas por semana")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    if anom:
        ax.legend(loc="upper right")
    nome = _salvar(fig, "01_volume_semanal.png")
    med = float(np.median(vol[1:-1]))
    quedas = "; ".join(f"{semanas[i].strftime('%d/%m/%Y')} ({vol[i]} conversas)" for i in anom) or "nenhuma"
    txt = (f"O volume semanal tem mediana de {_fmt(med)} conversas (de {_fmt(min(vol[1:-1]))} a {_fmt(max(vol[1:-1]))}, "
           f"sem as semanas parciais das pontas); semanas com queda forte (menos da metade das vizinhas): {quedas}. "
           f"Queda de volume pode ser indisponibilidade do serviço ou fim de um pico de interesse; não é lida como mudança de comportamento do usuário.")
    return nome, txt


def fig_concentracao_ip(conn) -> tuple[str, str]:
    cont = [int(r[0]) for r in _consultar(conn, "SELECT count(*) FROM stg.conversa GROUP BY hashed_ip")]
    cont.sort(reverse=True)
    n_ips, total = len(cont), sum(cont)
    acum = np.cumsum(cont) / total
    x = np.arange(1, n_ips + 1) / n_ips
    fig, ax = plt.subplots(figsize=TAMANHO, layout="constrained")
    ax.plot(x * 100, acum * 100, color=COR, lw=2.6)
    ax.plot([0, 100], [0, 100], color=COR_CINZA, ls="--", lw=1.2, label="todos iguais")
    ax.set_xlabel("% dos IPs, dos mais ativos")
    ax.set_ylabel("% acumulado das conversas")
    ax.legend(loc="lower right")
    nome = _salvar(fig, "02_concentracao_ip.png")
    top1 = max(1, round(n_ips * 0.01))
    txt = (f"Há {_fmt(n_ips)} IPs distintos; o 1% mais ativo ({top1} IPs) responde por {_pct(participacao_topo(cont, top1), 0)} das "
           f"conversas e o IP mais ativo sozinho por {_pct(cont[0] / total)}. A mediana é de {int(np.median(cont))} conversa por IP: "
           f"IPs de volume anômalo precisam ficar fora do modelo principal.")
    return nome, txt


def fig_retorno_semanal(conn) -> tuple[str, str]:
    linhas = _consultar(conn, """
        SELECT periodo, novos, taxa, ic_inf, ic_sup, taxa_mm4, amostra_suficiente
        FROM mart.agg_retencao_periodo WHERE granularidade = 'semana' AND madura ORDER BY periodo""")
    per = [r[0] for r in linhas]
    taxa = np.array([float(r[2]) for r in linhas])
    inf = np.array([float(r[3]) for r in linhas])
    sup = np.array([float(r[4]) for r in linhas])
    ok = np.array([bool(r[6]) for r in linhas])
    mm4 = [float(r[5]) if r[5] is not None else np.nan for r in linhas]
    fig, ax = plt.subplots(figsize=TAMANHO, layout="constrained")
    ax.errorbar([p for p, o in zip(per, ok) if o], taxa[ok] * 100,
                yerr=[(taxa - inf)[ok] * 100, (sup - taxa)[ok] * 100], fmt="o", ms=4, color=COR, ecolor=COR_CLARA,
                elinewidth=1.2, alpha=0.9, label="semana")
    ax.errorbar([p for p, o in zip(per, ok) if not o], taxa[~ok] * 100, yerr=[(taxa - inf)[~ok] * 100, (sup - taxa)[~ok] * 100],
                fmt="o", ms=4, color=COR_CINZA, ecolor=COR_GRADE, elinewidth=1.2, label="pouca gente")
    ax.plot(per, np.array(mm4) * 100, color=COR_DESTAQUE, lw=2.4, label="média de 4 semanas")
    ax.set_ylabel("% que voltou em 7 dias")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, columnspacing=0.8, handletextpad=0.3)
    nome = _salvar(fig, "03_retorno_semanal.png")
    larg = (sup - inf)[ok] * 100
    mm_validas = [m for m in mm4 if not np.isnan(m)]
    txt = (f"Entre as {int(ok.sum())} semanas maduras com n suficiente, a faixa de incerteza de cada ponto tem em média "
           f"{larg.mean():.0f} p.p. de largura: a variação semana a semana é em grande parte ruído. A média móvel de 4 semanas "
           f"fica entre {_pct(min(mm_validas), 0)} e {_pct(max(mm_validas), 0)}.")
    return nome, txt


def fig_turnos(conn) -> tuple[str, str]:
    dados = _consultar(conn, """
        SELECT least(n_turnos, 10) AS t, count(*) FROM stg.conversa WHERE conta_como_uso GROUP BY 1 ORDER BY 1""")
    ts = [int(d[0]) for d in dados]
    ns = [int(d[1]) for d in dados]
    total = sum(ns)
    fig, ax = plt.subplots(figsize=TAMANHO, layout="constrained")
    ax.bar([str(t) if t < 10 else "10+" for t in ts], [n / total * 100 for n in ns], color=COR, width=0.7)
    ax.set_xlabel("turnos da conversa")
    ax.set_ylabel("% das conversas")
    nome = _salvar(fig, "04_turnos.png")
    um = ns[ts.index(1)] / total
    ate3 = sum(n for t, n in zip(ts, ns) if t <= 3) / total
    txt = (f"{_pct(um, 0)} das conversas que contam como uso têm um único turno e {_pct(ate3, 0)} têm até três: o engajamento "
           f"dentro da conversa é curto e vem depois da resposta, por isso entra como sinal de engajamento e não como fator do assistente.")
    return nome, txt


def fig_tema(conn) -> tuple[str, str] | None:
    dados = _consultar(conn, """
        SELECT tema, count(*), count(*) FILTER (WHERE voltou_7d)
        FROM mart.fct_primeira_experiencia WHERE elegivel GROUP BY 1 ORDER BY 2 DESC""")
    if len([d for d in dados if d[0] != "não classificado"]) < 2:
        return None  # tema ainda não classificado (seed da T-205 ausente): não há o que mostrar
    ok = [d for d in dados if d[1] >= int(_consultar(conn, "SELECT ops.param('n_minimo')")[0][0])]
    rot = [d[0] for d in ok]
    taxa = np.array([d[2] / d[1] for d in ok])
    ics = [wilson(int(d[2]), int(d[1])) for d in ok]
    fig, ax = plt.subplots(figsize=TAMANHO, layout="constrained")
    y = np.arange(len(ok))
    ax.grid(False)
    ax.grid(True, axis="x")
    ax.barh(y, taxa * 100, xerr=[[(t - i[0]) * 100 for t, i in zip(taxa, ics)], [(i[1] - t) * 100 for t, i in zip(taxa, ics)]],
            color=COR, ecolor=COR_CLARA, height=0.62, error_kw={"elinewidth": 1.4})
    ax.set_yticks(y, [r for r in rot], fontsize=FONTE - 3)
    ax.invert_yaxis()
    ax.set_xlabel("% que voltou em 7 dias")
    nome = _salvar(fig, "05_retorno_por_tema.png")
    i_max, i_min = int(np.argmax(taxa)), int(np.argmin(taxa))
    separados = ics[i_max][0] > ics[i_min][1]
    txt = (f"O tema com maior retorno é '{rot[i_max]}' ({_pct(taxa[i_max], 0)}) e o menor é '{rot[i_min]}' ({_pct(taxa[i_min], 0)}); "
           + ("os intervalos não se sobrepõem." if separados else "os intervalos se sobrepõem: não dá para afirmar diferença só com este corte."))
    return nome, txt


def fig_idioma(conn) -> tuple[str, str]:
    cont = _consultar(conn, """
        SELECT idioma_pergunta_1, count(*) FROM stg.conversa WHERE conta_como_uso GROUP BY 1 ORDER BY 2 DESC LIMIT 6""")
    total = int(_consultar(conn, "SELECT count(*) FROM stg.conversa WHERE conta_como_uso")[0][0])
    faixas = _consultar(conn, """
        SELECT faixa_chars_pergunta, count(*), count(*) FILTER (WHERE idioma_divergente)
        FROM mart.fct_primeira_experiencia WHERE elegivel GROUP BY 1""")
    ordem = ["até 30", "31–100", "101–400", "mais de 400"]
    faixas = sorted(faixas, key=lambda r: ordem.index(r[0]))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=TAMANHO, layout="constrained")
    a1.grid(False)
    a1.grid(True, axis="x")
    a1.barh([_nome_idioma(c[0]) for c in cont][::-1], [c[1] / total * 100 for c in cont][::-1], color=COR, height=0.65)
    a1.set_xlabel("% das conversas, por idioma")
    a1.tick_params(axis="y", labelsize=FONTE - 2)
    taxas = [f[2] / f[1] for f in faixas]
    a2.bar([f[0] for f in faixas], [t * 100 for t in taxas], color=[COR_DESTAQUE if i == 0 else COR for i in range(len(faixas))], width=0.65)
    a2.set_xlabel("caracteres da 1ª pergunta")
    a2.set_ylabel("% de idioma trocado")
    a2.tick_params(axis="x", labelsize=FONTE - 3)
    nome = _salvar(fig, "06_idioma.png")
    resto = faixas[1:]
    taxa_resto = sum(f[2] for f in resto) / sum(f[1] for f in resto)
    txt = (f"{cont[0][0]} responde por {_pct(cont[0][1] / total, 0)} das conversas. O idioma da resposta difere do da pergunta em "
           f"{_pct(taxas[0], 0)} das perguntas de até 30 caracteres contra {_pct(taxa_resto, 0)} nas mais longas: em pergunta curta "
           f"isso é sobretudo erro de detecção, então o fator 'idioma divergente' é restrito a perguntas com mais de 30 caracteres.")
    return nome, txt


# ----------------------------------------------------------------------------------------------- qualidade dos dados
def problemas_qualidade(conn) -> list[tuple[str, int, float, str]]:
    import duckdb

    q = lambda s: _consultar(conn, s)[0]  # noqa: E731
    total = int(q("SELECT count(*) FROM stg.conversa")[0])
    vol = [int(r[1]) for r in _volume_semanal(conn)]
    n_sem = len(vol)
    anom = semanas_anomalas(vol)
    vazia, sem_uso, hash_rep, ip_mudou, redacted = (int(x) for x in q(
        "SELECT count(*) FILTER (WHERE pergunta_vazia), count(*) FILTER (WHERE NOT conta_como_uso), "
        "count(*) FILTER (WHERE hash_repetido), count(*) FILTER (WHERE ip_mudou), count(*) FILTER (WHERE redacted) FROM stg.conversa"))
    top_ip = int(q("SELECT max(c) FROM (SELECT count(*) AS c FROM stg.conversa GROUP BY hashed_ip) t")[0])
    anomalo_conv, anomalo_ips = (int(x) for x in q("""
        WITH ip AS (SELECT hashed_ip, count(*) AS n, count(DISTINCT user_agent) AS uas FROM stg.conversa GROUP BY 1)
        SELECT coalesce(sum(n), 0), count(*) FROM ip
        WHERE n >= ops.param('limiar_conversas_ip')::int OR uas >= ops.param('limiar_uas_ip')::int"""))
    curtas = int(q("SELECT count(*) FROM stg.conversa WHERE conta_como_uso AND idioma_divergente "
                   "AND chars_pergunta_1 <= 30")[0])
    uso = total - sem_uso
    snap = Path(os.environ.get("BRUTO_CAMINHO", RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"))
    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    toxic = int(con.execute(f"SELECT count(*) FILTER (WHERE toxic) FROM read_parquet('{snap.as_posix()}')").fetchall()[0][0])
    con.close()
    return [
        ("Pergunta vazia na 1ª mensagem", vazia, vazia / total,
         "Mantida na base; a conversa só conta como uso se a pessoa escreveu alguma mensagem."),
        ("Conversa sem nenhuma mensagem do usuário (não conta como uso)", sem_uso, sem_uso / total,
         "Fica fora das pessoas e das voltas; aparece na tela de confiança. Também testamos contar tudo."),
        ("Conteúdo repetido (hash da conversa repetido)", hash_rep, hash_rep / total,
         "Mantidas, identificadas por turn_identifier; conversation_hash não é chave."),
        ("Endereço de rede muda no meio da conversa", ip_mudou, ip_mudou / total,
         "Usa o endereço mais comum da conversa; efeito pequeno, registrado como limite da forma de identificar a pessoa."),
        ("Idioma divergente em pergunta curta (≤ 30 caracteres): provável erro de detecção", curtas, curtas / uso,
         "A comparação de 'resposta em outro idioma' só usa perguntas com mais de 30 caracteres (ver figura 06)."),
        ("Semanas com queda forte de volume", len(anom), len(anom) / n_sem,
         "Possível indisponibilidade do serviço; mantidas, com aviso nas telas e leitura cuidadosa do retorno."),
        ("Conversas do endereço de rede mais ativo", top_ip, top_ip / total,
         "Uso com cara de robô: o endereço fica fora da análise principal e entra em 'Incluindo uso com cara de robô'."),
        (f"Conversas de endereços com uso com cara de robô ({anomalo_ips} endereços)", anomalo_conv, anomalo_conv / total,
         "Ficam fora das pessoas que entram na conta; testamos também incluindo esses endereços."),
        ("Conversas com dado pessoal ocultado pelos autores (redacted)", redacted, redacted / total,
         "Mantidas; o texto já veio sem os dados pessoais."),
        ("Conversas tóxicas marcadas na base (os autores removeram as tóxicas desta versão)", toxic, toxic / total,
         "Nenhuma marcada: os autores retiraram as ofensivas, o que pode ter escondido voltas. Registrado como limite (dado que falta)."),
    ]


def figuras_sem_conclusao(pasta: Path) -> list[str]:
    """Nomes de PNG da pasta que não têm linha em conclusoes.md (a EDA só aceita gráfico que leva a uma conclusão)."""
    arq = pasta / "conclusoes.md"
    texto = arq.read_text(encoding="utf-8") if arq.is_file() else ""
    return sorted(p.name for p in pasta.glob("*.png") if f"`{p.name}`:" not in texto)


# ----------------------------------------------------------------------------------------------- orquestração
def gerar(conn: psycopg.Connection) -> dict:
    """Gera as figuras, `conclusoes.md` e grava resultado.problema_qualidade. Devolve um resumo com contagens."""
    _estilo()
    PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)
    for antigo in PASTA_FIGURAS.glob("*.png"):
        antigo.unlink()  # figura de uma versão anterior sem conclusão não pode sobrar
    geradores = [fig_volume, fig_concentracao_ip, fig_retorno_semanal, fig_turnos, fig_tema, fig_idioma]
    pares = [r for r in (g(conn) for g in geradores) if r is not None]
    assert len(pares) <= MAX_FIGURAS
    linhas = ["# Conclusão de cada figura", "",
              "Cada figura tem uma frase de conclusão; os números saem do cálculo que gerou a figura (`python -m analise eda`).", ""]
    linhas += [f"- `{nome}`: {txt}" for nome, txt in pares]
    (PASTA_FIGURAS / "conclusoes.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    probs = problemas_qualidade(conn)
    substituir(conn, "problema_qualidade", ["problema", "contagem", "percentual", "tratamento"],
               [(p, c, round(f, 6), t) for p, c, f, t in probs])
    return {"figuras": [n for n, _ in pares], "problemas": probs}
