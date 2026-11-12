import type { ReactNode } from "react";
import { Navegacao } from "@/components/Navegacao";
import { Rodape } from "@/components/Rodape";
import { t } from "@/lib/mensagens";
import "./globals.css";

export const metadata = { title: t("app.titulo") };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen pb-16">
        <header className="bg-white px-4 pt-3 text-sm font-semibold text-slate-800">{t("app.titulo")}</header>
        <Navegacao />
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        <Rodape />
      </body>
    </html>
  );
}
