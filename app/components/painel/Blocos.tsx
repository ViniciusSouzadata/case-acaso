import type { ReactNode } from "react";
import { t } from "@/lib/mensagens";

/** Peças comuns dos painéis que abrem ao clicar: número em destaque, até 3 frases curtas e o bloco técnico recolhido. */

/** Número (ou mini-gráfico) em destaque, com um rótulo curto ao lado. */
export function Destaque({ valor, rotulo, children }: { valor?: string; rotulo?: string; children?: ReactNode }) {
  return (
    <div className="flex items-baseline gap-3">
      {valor ? <span className="font-display text-4xl font-semibold leading-none tracking-tight text-tinta tabular-nums">{valor}</span> : null}
      {rotulo ? <span className="text-sm text-slate-700">{rotulo}</span> : null}
      {children}
    </div>
  );
}

/** Frases curtas, uma por parágrafo. */
export function Frases({ itens }: { itens: ReactNode[] }) {
  return (
    <div className="space-y-2 text-sm text-slate-800">
      {itens.map((f, i) => (
        <p key={i}>{f}</p>
      ))}
    </div>
  );
}

/** Lê as frases "<prefixo>.1", "<prefixo>.2"… do arquivo de mensagens, até faltar uma. */
export function frasesDe(prefixo: string, vars: Record<string, string | number> = {}): string[] {
  const saida: string[] = [];
  for (let i = 1; i < 10; i++) {
    const chave = `${prefixo}.${i}`;
    const f = t(chave, vars);
    if (f === chave) break;
    saida.push(f);
  }
  return saida;
}

/** Tudo o que não cabe na leitura rápida: fórmulas, nomes internos, tabelas. */
export function Tecnico({ children, titulo }: { children: ReactNode; titulo?: string }) {
  return (
    <details className="rounded-lg border border-[#e3e0f3] bg-white p-2 text-sm">
      <summary className="cursor-pointer font-medium text-violeta-escuro">{titulo ?? t("glossario.tecnicoTitulo")}</summary>
      <div className="mt-2 space-y-3 text-slate-800">{children}</div>
    </details>
  );
}

/** Campo do bloco técnico: rótulo pequeno e o texto. */
export function CampoTecnico({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold text-violeta-escuro">{rotulo}</div>
      <div className="mt-0.5 text-slate-900">{children}</div>
    </div>
  );
}
