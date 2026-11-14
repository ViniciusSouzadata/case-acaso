// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PaginaDados from "@/app/dados/page";
import { veredicto } from "@/lib/qualidade";
import { formatarDataHora } from "@/lib/regras";

const mock = vi.hoisted(() => ({ corpo: null as unknown }));
vi.mock("@/lib/useApi", () => ({
  // o dicionário (dentro de "Ver detalhes") pede outra rota e espera uma lista
  useApi: (url: string) => ({ estado: "ok", corpo: { dados: url.includes("qualidade") ? mock.corpo : [], meta: {} } }),
}));

afterEach(cleanup);

const lote = { lote_id: 1, iniciado_em: "2026-11-11 22:30:16+00", terminado_em: "2026-11-11 22:30:37+00", fonte: "x", linhas_lidas: 11621, linhas_gravadas: 11621, linhas_rejeitadas: 0, versao_definicao: "1.0.0", status: "sucesso" };
const problema = { problema: "IP muda no meio da conversa", contagem: 175, percentual: 0.015, tratamento: "Usa o IP mais comum." };
const rec = (metrica: string, ok: boolean) => ({ metrica, valor_bruto: 10, valor_mart: ok ? 10 : 9, diferenca: ok ? 0 : 1, tolerancia: 0, ok });

describe("veredicto", () => {
  it("só diz ok com conferência e todas batendo", () => {
    expect(veredicto(true, [rec("a", true)]).v).toBe("ok");
    expect(veredicto(true, [rec("a", true), rec("b", false)])).toEqual({ v: "falha", falhas: 1, total: 2 });
    expect(veredicto(true, []).v).toBe("sem_conferencia");
    expect(veredicto(false, []).v).toBe("sem_lote");
  });
});

describe("data", () => {
  it("converte para o horário de Brasília", () => {
    expect(formatarDataHora("2026-11-11 22:30:37.04+00")).toContain("11/11/2026");
    expect(formatarDataHora(null)).toBeNull();
    expect(formatarDataHora("lixo")).toBeNull();
  });
});

describe("Tela 3 — Confiança nos dados (painel)", () => {
  beforeEach(() => {
    mock.corpo = { lote, reconciliacao: [rec("elegiveis", true), rec("voltaram", false)], problemas: [problema], validacao: [] };
  });

  it("mostra a carga em cartões, a frase de confiança e a barra do problema", () => {
    render(<PaginaDados />);
    expect(screen.getByText("Conversas lidas")).toBeTruthy();
    expect(screen.getByText("11.621")).toBeTruthy();
    expect(screen.getByText(/0 descartadas/)).toBeTruthy();
    expect(screen.getByTestId("conferencias").textContent).toBe("1 de 2");
    expect(screen.getByTestId("frase-confianca").textContent).toContain("1 de 2");
    expect(document.querySelectorAll("[data-problema]").length).toBe(1);
  });

  it("conferências uma a uma ficam atrás de 'Ver detalhes', com ok/falha", () => {
    render(<PaginaDados />);
    expect(document.querySelectorAll("[data-ok]").length).toBe(0);
    fireEvent.click(screen.getAllByRole("button", { name: /Ver detalhes/ })[0]!);
    expect([...document.querySelectorAll("[data-ok]")].map((i) => i.getAttribute("data-ok"))).toEqual(["true", "false"]);
  });

  it("clicar na barra abre contagem e tratamento do problema", () => {
    render(<PaginaDados />);
    fireEvent.click(document.querySelector("[data-problema] button")!);
    const d = screen.getByRole("dialog");
    expect(d.textContent).toMatch(/175 conversas \(1,5%\)/);
    expect(d.textContent).toMatch(/Usa o IP mais comum/);
  });

  it("sem conferência e sem validação: diz isso, não finge que está tudo certo", () => {
    mock.corpo = { lote, reconciliacao: [], problemas: [], validacao: [] };
    render(<PaginaDados />);
    expect(screen.getByTestId("frase-confianca").textContent).toContain("ainda não há conferência");
    expect(screen.getByTestId("conferencias").textContent).toBe("—");
  });

  it("acerto do classificador aparece com a taxa e o n; tema vem marcado como só descritivo", () => {
    const v = (classificador: string) => ({ classificador, n: 200, acuracia: 0.9, kappa: 0.8, detalhe_json: null, versao_prompt: null, modelo: "m" });
    mock.corpo = { lote, reconciliacao: [rec("a", true)], problemas: [], validacao: [v("tema"), v("recusa")] };
    render(<PaginaDados />);
    expect(screen.getAllByText("90%").length).toBe(2);
    expect(screen.getAllByText(/em 200 conversas conferidas à mão/).length).toBe(2);
    expect(screen.getByText(/o assunto é só ilustrativo/)).toBeTruthy();
  });

  it("quadro 'mostra / nunca mostra' sempre presente", () => {
    render(<PaginaDados />);
    expect(screen.getByText("O painel nunca mostra")).toBeTruthy();
    expect(screen.getByText("Texto de nenhuma conversa")).toBeTruthy();
    expect(screen.getByText(/nem navegador de ninguém/)).toBeTruthy();
  });
});
