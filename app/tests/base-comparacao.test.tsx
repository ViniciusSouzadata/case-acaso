// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BlocoSemana } from "@/components/BlocoSemana";
import { DiferencaSemana } from "@/components/graficos/DiferencaSemana";
import type { ResumoSemanaApi } from "@/lib/graficos";
import { baseSeguinte, fraseProblemaEndereco } from "@/lib/painel";
import { formatarInt, formatarPct } from "@/lib/regras";

const mock = vi.hoisted(() => ({ resumo: null as unknown }));
vi.mock("@/lib/useApi", () => ({ useApi: () => ({ estado: "ok", corpo: { dados: { resumo: mock.resumo, segmentos: [] }, meta: {} } }) }));

afterEach(cleanup);

const base = (descricao: string, nBase: number, nSemana: number): ResumoSemanaApi => ({
  semana: "x", base_descricao: descricao, n_base: nBase, n_semana: nSemana, taxa_base: 0.244, taxa_semana: 0.167,
  delta_pp: -7.7, mix_pp: -0.6, taxa_pp: -7.1, p_valor: 0.13, conclusao: "c",
});
const SEGUINTES = base("4 semanas seguintes (a semana é do início da coleta; não há semanas anteriores limpas) (08/05/2023 a 29/05/2023)", 340, 84);
const ANTERIORES = base("4 semanas anteriores (23/10/2023 a 13/11/2023)", 410, 95);

describe("base de comparação da semana (anteriores × seguintes)", () => {
  it("baseSeguinte lê o campo que descreve a base", () => {
    expect(baseSeguinte(SEGUINTES)).toBe(true);
    expect(baseSeguinte(ANTERIORES)).toBe(false);
    expect(baseSeguinte({ base_descricao: null })).toBe(false);
  });

  it("01/05 (início da coleta): a legenda e a frase dizem 'seguintes'", () => {
    mock.resumo = SEGUINTES;
    render(<BlocoSemana inicial="2023-05-01" />);
    expect(screen.getByText("de cada 100 voltaram: semanas seguintes → nessa semana")).toBeTruthy();
    expect(screen.getByText("Comparada com as 4 semanas seguintes (340 pessoas); 84 pessoas nessa semana.")).toBeTruthy();
    expect(document.body.textContent).not.toContain("4 semanas anteriores");
    expect(document.body.textContent).not.toContain("antes → nessa semana");
  });

  it("20/11: continua 'antes' e 'anteriores'", () => {
    mock.resumo = ANTERIORES;
    render(<BlocoSemana inicial="2023-11-20" />);
    expect(screen.getByText("de cada 100 voltaram: antes → nessa semana")).toBeTruthy();
    expect(screen.getByText("Comparada com as 4 semanas anteriores (410 pessoas); 95 pessoas nessa semana.")).toBeTruthy();
  });

  it("o bloco da tela (DiferencaSemana) também segue o campo", () => {
    const { rerender } = render(<DiferencaSemana resumo={SEGUINTES} />);
    expect(screen.getByText(/semanas seguintes → nessa semana/)).toBeTruthy();
    rerender(<DiferencaSemana resumo={ANTERIORES} />);
    expect(screen.getByText(/antes → nessa semana/)).toBeTruthy();
  });
});

describe("frases do detalhe dos problemas de endereço", () => {
  it("usam os números da API", () => {
    const f = (problema: string, contagem: number, percentual: number) => fraseProblemaEndereco({ problema, contagem, percentual }, formatarInt, formatarPct);
    expect(f("Conversas de endereços com uso com cara de robô (7 endereços de rede)", 3284, 0.2826)).toBe("7 endereços de rede fizeram 3.284 conversas (28,3%).");
    expect(f("Conversas do endereço de rede mais ativo", 1557, 0.134)).toBe("Um único endereço fez 1.557 conversas (13,4%).");
    expect(f("Pergunta vazia", 141, 0.012)).toBeNull();
  });
});
