import type { ReactNode } from "react";
import localFont from "next/font/local";
import { Navegacao } from "@/components/Navegacao";
import { Rodape } from "@/components/Rodape";
import { t } from "@/lib/mensagens";
import "./globals.css";

// Fontes de licença aberta (OFL-1.1) embutidas no projeto: nenhuma requisição externa em tempo de execução nem no build.
const sora = localFont({ src: "./fonts/sora-latin-wght-normal.woff2", weight: "100 800", variable: "--font-sora", display: "swap" });
const instrument = localFont({ src: "./fonts/instrument-sans-latin-wght-normal.woff2", weight: "400 700", variable: "--font-instrument", display: "swap" });
const plex = localFont({ src: "./fonts/ibm-plex-mono-latin-400-normal.woff2", weight: "400", variable: "--font-plex", display: "swap" });

export const metadata = { title: t("app.titulo") };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${sora.variable} ${instrument.variable} ${plex.variable}`}>
      <body className="min-h-screen pb-16">
        <div className="cabecalho bg-tinta">
          <div className="mx-auto max-w-5xl px-4 pt-4">
            <p className="font-display text-base font-semibold tracking-tight text-papel">{t("app.titulo")}</p>
          </div>
          <Navegacao />
        </div>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <Rodape />
      </body>
    </html>
  );
}
