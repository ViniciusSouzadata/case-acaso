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
    <nav aria-label="Telas" className="flex flex-wrap gap-1">
      {ABAS.map((a) => {
        const ativa = a.href === "/" ? atual === "/" : atual.startsWith(a.href);
        return (
          <Link
            key={a.href}
            href={a.href}
            aria-current={ativa ? "page" : undefined}
            className={`border-b-2 px-3 py-3.5 text-sm ${ativa ? "border-violeta-claro font-semibold text-papel" : "border-transparent text-white/70 hover:text-papel"}`}
          >
            {t(a.chave)}
          </Link>
        );
      })}
    </nav>
  );
}
