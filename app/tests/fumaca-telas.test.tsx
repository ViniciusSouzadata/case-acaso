// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { varrer } from "./helpers/varredura";

// T-406 — fumaça ponta a ponta das telas contra o banco REAL: cada tela é renderizada com dados vindos das rotas da API
// (papel app_ro). Só roda com DATABASE_URL. Ex.: DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx vitest run tests/fumaca-telas
const temBanco = Boolean(process.env.DATABASE_URL);

describe.skipIf(!temBanco)("fumaça das telas contra o banco real", () => {
  const original = globalThis.fetch;

  beforeAll(() => {
    // o fetch das telas é desviado para os handlers de rota (sem subir servidor)
    vi.stubGlobal("fetch", async (entrada: RequestInfo | URL) => {
      const url = new URL(String(entrada), "http://localhost");
      const modulo = (await import(/* @vite-ignore */ `@/app${url.pathname}/route`)) as { GET: (r: Request) => Promise<Response> };
      return modulo.GET(new Request(url.toString()));
    });
  });

  afterEach(cleanup);

  afterAll(async () => {
    vi.stubGlobal("fetch", original);
    const { pool } = await import("@/lib/db");
    await pool().end();
  });

  const semDadoSensivel = () => {
    const html = document.body.innerHTML;
    expect(varrer(html), "dado sensível no HTML da tela").toEqual([]);
    // os nomes dos campos podem aparecer em texto explicativo (ex.: "conversation_hash não é chave"); o que não pode é o VALOR (varredura acima)
  };

  it("Tela 1 (Retenção): números oficiais, frase de leitura e glossário pelo 'i'", async () => {
    const { default: Pagina } = await import("@/app/page");
    render(<Pagina />);
    await waitFor(() => expect(document.body.textContent).toContain("2.372"), { timeout: 20000 });
    // a frase vem de outra requisição que o cartão: espera por ela, em vez de supor que já chegou
    await waitFor(() => expect(screen.getByTestId("frase-resposta").textContent?.length).toBeGreaterThan(20), { timeout: 20000 });

    const botoes = screen.getAllByRole("button", { name: /O que é este número/i });
    expect(botoes.length).toBeGreaterThan(0);
    fireEvent.click(botoes[0]!);
    const dialogo = await screen.findByRole("dialog");
    await waitFor(() => expect(dialogo.textContent).toMatch(/Defini|Fórmula/i), { timeout: 20000 });
    expect(dialogo.querySelector("pre")).not.toBeNull();
    semDadoSensivel();
  }, 60000);

  it("Tela 2 (O que faz voltar): floresta com dados reais e frase-resposta", async () => {
    const { default: Pagina } = await import("@/app/fatores/page");
    render(<Pagina />);
    await waitFor(() => expect(document.querySelectorAll("[data-fator]").length).toBeGreaterThan(0), { timeout: 20000 });
    await waitFor(() => expect(screen.getByTestId("frase-resposta").textContent).toMatch(/comparações/), { timeout: 20000 });
    semDadoSensivel();
  }, 60000);

  it("Tela 3 (Confiança nos dados): carga e problemas reais, quadro 'nunca mostra'", async () => {
    const { default: Pagina } = await import("@/app/dados/page");
    render(<Pagina />);
    await waitFor(() => expect(document.body.textContent).toMatch(/linhas lidas/), { timeout: 20000 });
    await waitFor(() => expect(document.body.textContent).toContain("O texto de nenhuma conversa"), { timeout: 20000 });
    await waitFor(() => expect(screen.getByTestId("frase-confianca").textContent?.length).toBeGreaterThan(20), { timeout: 20000 });
    semDadoSensivel();
  }, 60000);
});
