"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { t } from "@/lib/mensagens";

const ABAS = [
  { href: "/", chave: "nav.retencao" },
  { href: "/fatores", chave: "nav.fatores" },
  { href: "/dados", chave: "nav.dados" },
] as const;

export function Navegacao() {
  const atual = usePathname();
  return (
    <nav aria-label="Telas" className="flex flex-wrap gap-1 border-b border-slate-200 bg-white px-4">
      {ABAS.map((a) => {
        const ativa = a.href === "/" ? atual === "/" : atual.startsWith(a.href);
        return (
          <Link
            key={a.href}
            href={a.href}
            aria-current={ativa ? "page" : undefined}
            className={`border-b-2 px-3 py-3 text-sm ${ativa ? "border-azul font-semibold text-azul" : "border-transparent text-slate-700 hover:text-azul"}`}
          >
            {t(a.chave)}
          </Link>
        );
      })}
    </nav>
  );
}
