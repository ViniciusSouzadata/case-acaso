"use client";

import { useEffect, useState } from "react";
import { LinhaDaFloresta } from "@/components/graficos/Floresta";
import { PainelLateral } from "@/components/PainelLateral";
import { DetalheBalanco } from "@/components/DetalheBalanco";
import { grupoEfetivo, prepararFloresta, type EfeitoApi, type GrupoFator, type LinhaFloresta } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { aCadaCem, efeitoDaLinha, nomeCurto, seloDaLinha, type Selo } from "@/lib/painel";

const GRUPOS: GrupoFator[] = ["assistente", "perfil", "engajamento", "descritivo"];
const LARANJA = "#ff6c0e";
const CINZA = "#8a8f98";
const CINZA_CLARO = "#c4c8d0";
const LINHAS_INICIAIS = 7;

const ESTILO_SELO: Record<Selo, string> = {
  sustenta: "bg-[#ffe9db] text-[#8a3a00]",
  acaso: "bg-[#f1efe8] text-slate-700",
  semDiferenca: "bg-slate-100 text-slate-700",
  pequena: "bg-slate-100 text-slate-700",
  descritivo: "bg-slate-100 text-slate-700",
};

function Trilha({ l }: { l: LinhaFloresta }) {
  const pos = l.ajustado ? l.pos.ajustado : l.pos.bruto;
  const destaque = seloDaLinha(l) === "sustenta";
  return (
    <div className="relative h-5" role="img" aria-label={l.leitura ?? nomeCurto(l.fator, l.nivel)}>
      <div className="absolute top-1/2 h-px w-full bg-slate-200" />
      <div className="absolute top-0 h-5 w-px bg-slate-500" style={{ left: `${l.pos.zero}%` }} />
      {pos ? (
        <>
          <div className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded" style={{ left: `${pos[0]}%`, width: `${Math.max(0.5, pos[2] - pos[0])}%`, background: destaque ? LARANJA : CINZA_CLARO, opacity: destaque ? 0.55 : 1 }} />
          <div
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2"
            style={{ left: `${pos[1]}%`, background: l.pequena ? "#fff" : destaque ? LARANJA : CINZA, borderColor: destaque ? LARANJA : CINZA }}
          />
        </>
      ) : null}
    </div>
  );
}

function LinhaRanking({ l, onAbrir, realcada }: { l: LinhaFloresta; onAbrir: () => void; realcada: boolean }) {
  const selo = seloDaLinha(l);
  const efeito = efeitoDaLinha(l);
  const numero = efeito === null ? t("painel.tela2.selo.pequena") : aCadaCem(efeito);
  const destaque = selo === "sustenta";
  const classeNumero = `whitespace-nowrap font-display text-sm font-semibold ${destaque ? "text-[#8a3a00]" : "text-slate-800"}`;
  return (
    <li className="entra" data-fator={l.fator} data-nivel={l.nivel} data-realce={realcada ? "sim" : undefined}>
      <button type="button" onClick={onAbrir} className={`grid w-full grid-cols-1 items-center gap-x-3 gap-y-1 rounded-lg px-2 py-1 text-left transition-colors hover:bg-[#ece8fc] focus-visible:outline focus-visible:outline-2 focus-visible:outline-violeta sm:grid-cols-[12rem_minmax(0,1fr)_8.75rem_8.5rem] ${realcada ? "bg-[#e6e0fb] ring-2 ring-violeta" : ""}`}>
        <div className="flex items-baseline justify-between gap-2 sm:block">
          <span className="text-sm font-medium text-tinta">{nomeCurto(l.fator, l.nivel)}</span>
          <span className={`${classeNumero} sm:hidden`}>{numero}</span>
        </div>
        <Trilha l={l} />
        <span className={`${classeNumero} hidden text-right sm:block`}>{numero}</span>
        <span className={`w-fit whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium sm:justify-self-start ${ESTILO_SELO[selo]}`}>{t(`painel.tela2.selo.${selo}`)}</span>
      </button>
    </li>
  );
}

/** Um ranking só: nome curto, barra com a margem de erro, número "a cada 100" e selo. Clicar na linha abre o detalhe. */
export function Ranking({ efeitos, realce = null }: { efeitos: EfeitoApi[]; realce?: { fator: string; nivel: string } | null }) {
  const [grupo, setGrupo] = useState<GrupoFator>("assistente");
  const [todos, setTodos] = useState(false);
  const [aberta, setAberta] = useState<LinhaFloresta | null>(null);
  const [ajuda, setAjuda] = useState(false);
  const { linhas } = prepararFloresta(efeitos, grupo);
  const visiveis = todos ? linhas : linhas.slice(0, LINHAS_INICIAIS);

  // cartão do achado realça a linha; se ela está em outro grupo (ou além das linhas iniciais), troca de aba / abre a lista
  useEffect(() => {
    if (!realce) return;
    const alvo = efeitos.find((e) => e.metodo === "logit_ame" && e.fator === realce.fator && e.nivel === realce.nivel);
    if (!alvo) return;
    const g = grupoEfetivo(alvo);
    if (g !== grupo) {
      setGrupo(g);
      setTodos(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [realce?.fator, realce?.nivel]);

  return (
    <section className="cartao p-4" aria-labelledby="rank-titulo">
      <h2 id="rank-titulo" className="sr-only">{t("painel.tela2.titulo")}</h2>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div role="tablist" aria-label="Grupos de fatores" className="flex flex-wrap gap-1">
          {GRUPOS.map((g) => (
            <button
              key={g}
              role="tab"
              type="button"
              aria-selected={grupo === g}
              onClick={() => { setGrupo(g); setTodos(false); }}
              className={`alvo rounded-full px-3 py-1 text-sm ${grupo === g ? "bg-violeta font-medium text-papel" : "bg-[#f1effc] text-slate-800 hover:bg-[#e6e2fa]"}`}
            >
              {t(`fatores.abas.${g}`)}
            </button>
          ))}
        </div>
        <button type="button" onClick={() => setAjuda(true)} className="alvo text-sm font-medium text-violeta hover:underline">{t("painel.tela2.ajuda")}</button>
      </div>

      <ul className={`mt-2 divide-y divide-[#efedf8] ${todos ? "max-h-[17.5rem] overflow-y-auto pr-1" : ""}`} role="tabpanel">
        {visiveis.map((l) => (
          <LinhaRanking key={l.chave} l={l} onAbrir={() => setAberta(l)} realcada={realce !== null && l.fator === realce.fator && l.nivel === realce.nivel} />
        ))}
      </ul>
      <div className="mt-1 flex items-center justify-between gap-2 px-2 text-xs text-slate-600">
        <span>{t("painel.tela2.eixo")}</span>
        {linhas.length > LINHAS_INICIAIS ? (
          <button type="button" onClick={() => setTodos(!todos)} className="alvo font-medium text-violeta hover:underline">
            {todos ? "Mostrar menos" : `Mostrar todos (${linhas.length})`}
          </button>
        ) : null}
      </div>

      {aberta ? (
        <PainelLateral titulo={nomeCurto(aberta.fator, aberta.nivel)} onFechar={() => setAberta(null)}>
          <div className="cartao p-4">
            <ul>
              <LinhaDaFloresta l={aberta} indice={0} />
            </ul>
          </div>
          <p className="text-sm text-slate-700">{t("fatores.explica")}</p>
        </PainelLateral>
      ) : null}
      {ajuda ? (
        <PainelLateral titulo={t("painel.tela2.ajudaTitulo")} onFechar={() => setAjuda(false)}>
          <p className="text-sm text-slate-800">{t("painel.tela2.ajudaTexto")}</p>
          <p className="text-sm text-slate-700">{t("fatores.explica")}</p>
          <p className="text-sm text-slate-700">{t(`fatores.abasAjuda.${grupo}`)}</p>
          <DetalheBalanco />
        </PainelLateral>
      ) : null}
    </section>
  );
}
