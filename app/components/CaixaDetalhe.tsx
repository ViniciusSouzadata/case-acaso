"use client";

import { createPortal } from "react-dom";
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties, type KeyboardEvent as TeclaReact, type ReactNode } from "react";
import { t } from "@/lib/mensagens";
import { MOV, useMovimentoReduzido } from "@/lib/movimento";

/** Último clique na página (ponto na tela). Clique feito pelo teclado não traz posição: vale o centro do elemento. */
let ultimoClique: { x: number; y: number } | null = null;
if (typeof window !== "undefined") {
  window.addEventListener(
    "click",
    (e) => {
      const alvo = e.target instanceof Element ? e.target.getBoundingClientRect() : null;
      ultimoClique = e.detail === 0 && alvo ? { x: alvo.left + alvo.width / 2, y: alvo.top + alvo.height / 2 } : { x: e.clientX, y: e.clientY };
    },
    true,
  );
}

const MS = 220;
const FOCAVEIS = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, summary, [tabindex]:not([tabindex="-1"])';
const [c1, c2, c3, c4] = MOV.curva.entrada;

/** Caixa de detalhes ("Ver detalhes", linhas, barras, dicionário…): fica no centro da tela, com o fundo esmaecido, e cresce a partir do ponto do clique.
 * Fecha com o botão, Esc ou clique fora; o foco volta ao elemento que abriu. `largo` é para detalhes com gráfico ou tabela. */
export function CaixaDetalhe({ titulo, onFechar, largo = false, children }: { titulo: string; onFechar: () => void; largo?: boolean; children: ReactNode }) {
  const idTitulo = useId();
  const reduzido = useMovimentoReduzido();
  const caixa = useRef<HTMLDivElement>(null);
  const botao = useRef<HTMLButtonElement>(null);
  const gatilho = useRef<Element | null>(null);
  const origem = useRef(ultimoClique);
  const [visivel, setVisivel] = useState(false);
  const [ponto, setPonto] = useState<string>("50% 50%");
  const fechando = useRef(false);

  // quem abriu (para devolver o foco) é lido antes de qualquer foco novo
  if (gatilho.current === null && typeof document !== "undefined") gatilho.current = document.activeElement;

  useLayoutEffect(() => {
    const c = caixa.current;
    if (c && origem.current) setPonto(`${Math.round(origem.current.x - c.offsetLeft)}px ${Math.round(origem.current.y - c.offsetTop)}px`);
    const q = requestAnimationFrame(() => setVisivel(true));
    return () => cancelAnimationFrame(q);
  }, []);

  // fundo parado enquanto a caixa está aberta; ao sair, o foco volta ao gatilho
  useEffect(() => {
    const antes = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    botao.current?.focus();
    const volta = gatilho.current;
    return () => {
      document.body.style.overflow = antes;
      if (volta instanceof HTMLElement && volta.isConnected) volta.focus();
    };
  }, []);

  const fechar = useCallback(() => {
    if (fechando.current) return;
    fechando.current = true;
    if (reduzido) {
      onFechar();
      return;
    }
    setVisivel(false);
    window.setTimeout(onFechar, MS - 20);
  }, [onFechar, reduzido]);

  useEffect(() => {
    const aoTecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") fechar();
    };
    window.addEventListener("keydown", aoTecla);
    return () => window.removeEventListener("keydown", aoTecla);
  }, [fechar]);

  // o foco não sai da caixa: Tab no último volta ao primeiro, Shift+Tab no primeiro vai ao último
  const prender = (e: TeclaReact<HTMLDivElement>) => {
    if (e.key !== "Tab" || !caixa.current) return;
    const itens = [...caixa.current.querySelectorAll<HTMLElement>(FOCAVEIS)].filter((i) => i.tagName === "SUMMARY" || !i.closest("details:not([open])"));  // dentro de "técnico" recolhido não há onde pôr o foco
    if (itens.length === 0) return;
    const primeiro = itens[0]!;
    const ultimo = itens[itens.length - 1]!;
    if (e.shiftKey && document.activeElement === primeiro) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primeiro.focus();
    } else if (!caixa.current.contains(document.activeElement)) {
      e.preventDefault();
      primeiro.focus();
    }
  };

  const transicao = reduzido ? `opacity ${MS}ms linear` : `opacity ${MS}ms cubic-bezier(${c1},${c2},${c3},${c4}), transform ${MS}ms cubic-bezier(${c1},${c2},${c3},${c4})`;
  const estiloCaixa: CSSProperties = { transformOrigin: ponto, opacity: visivel ? 1 : 0, transform: reduzido || visivel ? "none" : "scale(0.9)", transition: transicao };

  // fora da árvore da página: um ancestral com transform ou filtro prenderia o "fixed" ao miolo e deixaria cabeçalho e rodapé sem escurecer
  const tela = (
    <div
      data-testid="caixa-fundo"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-tinta/40 p-3"
      style={{ opacity: visivel ? 1 : 0, transition: `opacity ${MS}ms linear` }}
      onClick={(e) => {
        if (e.target === e.currentTarget) fechar();
      }}
    >
      <div
        ref={caixa}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        onKeyDown={prender}
        style={estiloCaixa}
        className={`flex max-h-[85vh] w-full flex-col overflow-hidden rounded-2xl border border-[#e3e0f3] bg-fundo shadow-2xl ${largo ? "max-w-[860px]" : "max-w-[520px]"}`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#e3e0f3] bg-papel px-5 py-3">
          <h2 id={idTitulo} className="font-display text-lg font-semibold text-tinta">{titulo}</h2>
          <button ref={botao} type="button" onClick={fechar} className="shrink-0 rounded-lg border border-violeta px-3 py-1 text-sm font-medium text-violeta hover:bg-violeta hover:text-papel">
            {t("painel.fechar")}
          </button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  );
  return typeof document === "undefined" ? null : createPortal(tela, document.body);
}
