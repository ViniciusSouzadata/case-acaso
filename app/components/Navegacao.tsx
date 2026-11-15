"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { MOV } from "@/lib/movimento";
import { t } from "@/lib/mensagens";
import { useNavegar } from "@/components/movimento/TransicaoPagina";

const ABAS = [
  { href: "/", chave: "nav.retencao" },
  { href: "/fatores", chave: "nav.fatores" },
  { href: "/dados", chave: "nav.dados" },
] as const;

/** Menu em pílulas: a pílula escura desliza até a tela escolhida (mola). */
export function Navegacao() {
  const atual = usePathname();
  const navegar = useNavegar();
  return (
    <nav aria-label="Telas" className="flex flex-wrap justify-center gap-1 rounded-full bg-[#eceaf6] p-1">
      {ABAS.map((a) => {
        const ativa = a.href === "/" ? atual === "/" : atual.startsWith(a.href);
        return (
          <Link
            key={a.href}
            href={a.href}
            aria-current={ativa ? "page" : undefined}
            onClick={(e) => {
              if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0 || ativa) return;
              e.preventDefault();
              navegar(a.href);
            }}
            className={`relative flex min-h-10 items-center rounded-full px-4 text-sm ${ativa ? "font-semibold text-papel" : "text-slate-700 hover:text-tinta"}`}
          >
            {ativa ? <motion.span layoutId="nav-pill" transition={MOV.pilula} className="absolute inset-0 rounded-full bg-tinta" /> : null}
            <span className="relative">{t(a.chave)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
