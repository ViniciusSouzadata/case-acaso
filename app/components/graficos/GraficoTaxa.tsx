"use client";

import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { faixasEras, faixasImaturas, type EraApi, type Granularidade, type LinhaGrafico } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useMovimentoReduzido } from "@/lib/movimento";
import { DicaCoorte } from "./DicaCoorte";

const VIOLETA = "#6a48eb";
const CINZA = "#8a8f98";
const CINZA_CLARO = "#aeb4bf"; // cada semana: pontos pequenos, para a média de 4 semanas ser a linha que se lê

interface PontoProps {
  cx?: number;
  cy?: number;
  payload?: LinhaGrafico;
}

const poucaGente = (l: LinhaGrafico) => !l.amostraOk || l.inicioColeta;

/** Visão por mês: ponto em cada mês (cheio violeta; vazado cinza se pouca gente). Visão por semana: ponto pequeno cinza-claro (vazado se pouca gente). */
function criarPonto(gran: Granularidade) {
  return function Ponto({ cx, cy, payload }: PontoProps) {
    if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
    if (poucaGente(payload)) return <circle cx={cx} cy={cy} r={gran === "mes" ? 4 : 3} fill="#fff" stroke={CINZA} strokeWidth={1.5} />;
    return gran === "mes" ? <circle cx={cx} cy={cy} r={3.5} fill={VIOLETA} stroke="#fff" strokeWidth={1} /> : <circle cx={cx} cy={cy} r={2.5} fill={CINZA_CLARO} />;
  };
}

function PontoAtivo({ cx, cy, payload }: PontoProps) {
  if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
  return <circle cx={cx} cy={cy} r={6} fill="#fff" stroke={poucaGente(payload) ? CINZA : VIOLETA} strokeWidth={3} />;
}

/** Teto do eixo: o menor múltiplo de 20 que cabe a faixa de margem de erro inteira (sem cortar). */
export function tetoEixo(linhas: LinhaGrafico[]): number {
  const topo = Math.max(...linhas.map((l) => (l.taxa === null ? 0 : (l.icBase ?? 0) + (l.icAltura ?? 0))), ...linhas.map((l) => l.mm4 ?? 0), 20);
  return Math.min(100, Math.ceil(topo / 20) * 20);
}

/** Marcas do eixo X: de 2 em 2 meses contando do último mês real para trás (a última marca cai no último mês e nenhum mês do meio é pulado). */
export function marcasMes(linhas: LinhaGrafico[]): string[] {
  return linhas.filter((_, i) => (linhas.length - 1 - i) % 2 === 0).map((l) => l.periodo);
}

/** Gráfico principal da Tela 1.
 * Mês: linha reta entre os meses, um ponto por mês e a margem de erro.
 * Semana: a linha forte é a média de 4 semanas; cada semana é um ponto pequeno cinza-claro (sem linha ligando) e a margem de erro fica clara. */
export function GraficoTaxa({
  linhas,
  altura = "h-60",
  granularidade = "mes",
  marcadas = [],
  selecionada,
  onEscolher,
  eras = [],
}: {
  linhas: LinhaGrafico[];
  altura?: string;
  granularidade?: Granularidade;
  /** semanas que a decomposição explica: marcadas no gráfico e clicáveis (só com amostra suficiente) */
  marcadas?: string[];
  selecionada?: string;
  onEscolher?: (periodo: string) => void;
  /** épocas do produto como faixas de fundo (só no painel de detalhe) */
  eras?: EraApi[];
}) {
  const anima = !useMovimentoReduzido();
  const semana = granularidade === "semana";
  const faixas = faixasEras(linhas, eras);
  // a área "ainda dentro dos 7 dias" começa no último ponto com taxa, para existir mesmo com um único período em andamento
  const imaturas = faixasImaturas(linhas).map((f) => {
    const i = linhas.findIndex((l) => l.periodo === f.x1);
    return i > 0 ? { ...f, x1: linhas[i - 1]!.periodo } : f;
  });
  const temMedia = linhas.some((l) => l.mm4 !== null);
  const temPoucaGente = linhas.some((l) => l.taxa !== null && poucaGente(l));
  const teto = tetoEixo(linhas);
  const ticksY = Array.from({ length: teto / 20 + 1 }, (_, i) => i * 20);
  // amostra pequena nunca vira ponto clicável "firme"
  const clicaveis = linhas.filter((l) => marcadas.includes(l.periodo) && l.amostraOk && l.taxa !== null);
  const escolher = (p: string | undefined) => {
    if (p && onEscolher && clicaveis.some((l) => l.periodo === p)) onEscolher(p);
  };
  const ponto = criarPonto(granularidade);
  return (
    <div>
      <div role="img" aria-label={t(semana ? "painel.tela1.graficoTitulo" : "painel.tela1.graficoTituloMes")} className={`${altura} w-full`}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={linhas} margin={{ top: 14, right: 24, bottom: 0, left: 0 }} onClick={(e) => escolher(typeof e?.activeLabel === "string" ? e.activeLabel : undefined)} style={clicaveis.length > 0 ? { cursor: "pointer" } : undefined}>
            <defs>
              <pattern id="hachura-painel" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="6" height="6" fill="#fff" />
                <line x1="0" y1="0" x2="0" y2="6" stroke={CINZA} strokeWidth="2" />
              </pattern>
            </defs>
            {faixas.map((f) => (
              <ReferenceArea key={f.era} x1={f.x1} x2={f.x2} fill={f.cor} fillOpacity={0.14} stroke="none" ifOverflow="extendDomain" />
            ))}
            {imaturas.map((f) => (
              <ReferenceArea key={`im-${f.x1}`} x1={f.x1} x2={f.x2} fill="url(#hachura-painel)" fillOpacity={0.9} stroke="none" label={{ value: t("painel.tela1.emAndamento"), position: "insideTopRight", fontSize: 10, fill: "#475569", stroke: "#fff", strokeWidth: 3, paintOrder: "stroke" }} />
            ))}
            <CartesianGrid stroke="#eef0f4" vertical={false} />
            <XAxis
              dataKey="periodo"
              tickFormatter={(p: string) => linhas.find((l) => l.periodo === p)?.rotulo ?? p}
              {...(semana ? { interval: "preserveStartEnd" as const, minTickGap: 48 } : { ticks: marcasMes(linhas), interval: 0 as const })}
              tick={{ fontSize: 11, fill: "#475569" }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <YAxis width={40} unit="%" tick={{ fontSize: 11, fill: "#475569" }} domain={[0, teto]} ticks={ticksY} allowDataOverflow tickLine={false} axisLine={false} />
            <Tooltip cursor={{ stroke: VIOLETA }} content={({ payload }) => (payload && payload[0] ? <DicaCoorte linha={payload[0].payload as LinhaGrafico} clicavel={clicaveis.some((l) => l.periodo === (payload[0]!.payload as LinhaGrafico).periodo)} /> : null)} />
            <Area type="linear" dataKey="icBase" stackId="ic" stroke="none" fill="transparent" isAnimationActive={false} connectNulls={false} legendType="none" />
            <Area type="linear" dataKey="icAltura" stackId="ic" stroke="none" fill={VIOLETA} fillOpacity={semana ? 0.07 : 0.16} isAnimationActive={anima} animationDuration={400} connectNulls={false} legendType="none" />
            {semana ? <Line type="linear" dataKey="mm4" stroke={VIOLETA} strokeWidth={2} dot={false} isAnimationActive={anima} animationDuration={400} connectNulls /> : null}
            <Line type="linear" dataKey="taxa" stroke={semana ? "none" : VIOLETA} strokeWidth={2} dot={ponto} activeDot={<PontoAtivo />} isAnimationActive={anima} animationDuration={400} connectNulls={false} />
            {clicaveis.map((l) => (
              <ReferenceDot
                key={`m-${l.periodo}`}
                x={l.periodo}
                y={l.taxa!}
                r={l.periodo === selecionada ? 7 : 6}
                fill={l.periodo === selecionada ? VIOLETA : "#fff"}
                stroke={VIOLETA}
                strokeWidth={3}
                ifOverflow="visible"
                style={{ cursor: "pointer" }}
                onClick={() => escolher(l.periodo)}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-700" aria-label="Legenda">
        {semana ? (
          <>
            {temMedia ? <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-0.5 w-4 bg-violeta" />{t("painel.tela1.legMedia")}</li> : null}
            <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: CINZA_CLARO }} />{t(temPoucaGente ? "painel.tela1.legSemana" : "painel.tela1.legSemanaSimples")}</li>
          </>
        ) : (
          <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-0.5 w-4 bg-violeta" />{t(temPoucaGente ? "painel.tela1.legTaxa" : "painel.tela1.legTaxaSimples")}</li>
        )}
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-3 w-4 rounded-sm bg-violeta/20" />{t("painel.tela1.legFaixa")}</li>
        {clicaveis.length > 0 ? <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-3 w-3 rounded-full border-[3px] border-violeta bg-white" />{t("painel.tela1.legMarcada")}</li> : null}
        {faixas.map((f) => (
          <li key={f.era} className="flex items-center gap-1.5">
            <span aria-hidden className="inline-block h-3 w-3 rounded-sm border border-slate-300" style={{ background: f.cor, opacity: 0.5 }} />
            {f.descricao}
          </li>
        ))}
      </ul>
    </div>
  );
}
