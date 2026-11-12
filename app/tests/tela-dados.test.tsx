// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PaginaDados from "@/app/dados/page";
import { veredicto } from "@/lib/qualidade";
import { formatarDataHora } from "@/lib/regras";

const mock = vi.hoisted(() => ({ corpo: null as unknown }));
vi.mock("@/lib/useApi", () => ({
  useApi: () => ({ estado: "ok", corpo: { dados: mock.corpo, meta: {} } }),
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

describe("Tela 3 — Confiança nos dados", () => {
  beforeEach(() => {
    mock.corpo = { lote, reconciliacao: [rec("elegiveis", true), rec("voltaram", false)], problemas: [problema], validacao: [] };
  });

  it("mostra a carga, a conferência com ok/falha, o problema com contagem e tratamento", () => {
    render(<PaginaDados />);
    expect(screen.getByText(/11\.621 linhas lidas/)).toBeTruthy();
    expect(screen.getByText(/0 linhas rejeitadas/)).toBeTruthy();
    const itens = document.querySelectorAll("[data-ok]");
    expect([...itens].map((i) => i.getAttribute("data-ok"))).toEqual(["true", "false"]);
    expect(screen.getByText(/175 \(1,5%\)/)).toBeTruthy();
    expect(screen.getByText(/Usa o IP mais comum/)).toBeTruthy();
    expect(screen.getByTestId("frase-confianca").textContent).toContain("1 de 2");
  });

  it("sem conferência e sem validação: diz isso, não finge que está tudo certo", () => {
    mock.corpo = { lote, reconciliacao: [], problemas: [], validacao: [] };
    render(<PaginaDados />);
    expect(screen.getByTestId("frase-confianca").textContent).toContain("ainda não há conferência");
    expect(screen.getByText(/ainda não foi feita/)).toBeTruthy();
  });

  it("validação do classificador aparece com acurácia e n", () => {
    mock.corpo = { lote, reconciliacao: [rec("a", true)], problemas: [], validacao: [{ classificador: "tema", n: 200, acuracia: 0.9, kappa: 0.8, detalhe_json: null, versao_prompt: null, modelo: null }] };
    render(<PaginaDados />);
    expect(screen.getByText(/acerta 90,0% das 200/)).toBeTruthy();
  });

  it("quadro 'mostra / nunca mostra' sempre presente", () => {
    render(<PaginaDados />);
    const quadro = screen.getByRole("heading", { name: /O que este painel mostra/ }).closest("section")!;
    expect(within(quadro).getByText(/O texto de nenhuma conversa/)).toBeTruthy();
    expect(within(quadro).getByText(/Endereço de rede/)).toBeTruthy();
  });
});
