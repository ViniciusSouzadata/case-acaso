import type { ReactNode } from "react";
import localFont from "next/font/local";
import { Navegacao } from "@/components/Navegacao";
import { TransicaoPagina } from "@/components/movimento/TransicaoPagina";
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
      <body className="min-h-screen pb-8">
        <TransicaoPagina
          cabecalho={
            <header className="cabecalho flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
              <p className="font-display text-base font-semibold tracking-tight text-tinta">{t("app.titulo")}</p>
              <Navegacao />
            </header>
          }
        >
          {children}
        </TransicaoPagina>
        <Rodape />
      </body>
    </html>
  );
}
