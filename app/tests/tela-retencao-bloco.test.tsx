// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { PontosSensibilidade } from "@/components/graficos/PontosSensibilidade";
import { montarCascata, pontosSensibilidade, resumoSensibilidade, type ResumoSemanaApi, type SensibilidadeApi } from "@/lib/graficos";

afterEach(cleanup);

const resumo: ResumoSemanaApi = {
  semana: "2023-05-01", base_descricao: "exemplo", n_base: 500, n_semana: 84,
  taxa_base: 0.25, taxa_semana: 0.17, delta_pp: -8, mix_pp: -1, taxa_pp: -7, p_valor: 0.03, conclusao: "x",
};

describe("cascata da semana", () => {
  it("a soma fecha: base + mix + taxa = semana", () => {
    const c = montarCascata(resumo)!;
    expect(c.fecha).toBe(true);
    const [base, mix, taxa, semana] = c.degraus;
    expect(base!.valor + mix!.valor + taxa!.valor).toBeCloseTo(semana!.valor);
  });

  it("os degraus encadeiam: cada um começa onde o anterior terminou", () => {
    const [base, mix, taxa, semana] = montarCascata(resumo)!.degraus;
    expect(mix!.de).toBe(base!.ate);
    expect(taxa!.de).toBe(mix!.ate);
    expect(taxa!.ate).toBeCloseTo(semana!.ate);
    expect(base!.de).toBe(0);
    expect(semana!.de).toBe(0);
  });

  it("detecta quando a soma NÃO fecha (não esconde a diferença)", () => {
    const c = montarCascata({ ...resumo, taxa_pp: -3 })!;
    expect(c.fecha).toBe(false);
    expect(c.diferenca).toBeCloseTo(4);
  });

  it("sem os números, não monta", () => {
    expect(montarCascata({ ...resumo, mix_pp: null })).toBeNull();
  });
});

const sens: SensibilidadeApi[] = [
  { definicao: "oficial", descricao: "Definição oficial.", usuarios: 2372, voltaram_7d: 566, taxa: 0.2386, ic_inf: 0.2219, ic_sup: 0.2562, delta_vs_oficial: 0 },
  { definicao: "outro_dia", descricao: "Voltou em outro dia.", usuarios: 2372, voltaram_7d: 400, taxa: 0.1686, ic_inf: 0.154, ic_sup: 0.184, delta_vs_oficial: -7 },
];

describe("sensibilidade", () => {
  it("escala comum e linha da oficial", () => {
    const { pontos } = pontosSensibilidade(sens);
    expect(pontos.every((p) => p.posInf <= p.posTaxa && p.posTaxa <= p.posSup)).toBe(true);
    expect(pontos[0]!.oficial).toBe(true);
    expect(pontos[1]!.posOficial).toBeCloseTo(pontos[0]!.posTaxa);
    expect(Math.min(...pontos.map((p) => p.posInf))).toBeGreaterThanOrEqual(0);
    expect(Math.max(...pontos.map((p) => p.posSup))).toBeLessThanOrEqual(100);
  });

  it("resumo do título", () => {
    expect(resumoSensibilidade(sens)).toEqual({ min: 0.1686, max: 0.2386 });
  });

  it("mostra nome simples, intervalo e diferença em relação à oficial", () => {
    render(<PontosSensibilidade linhas={sens} />);
    expect(screen.getByText("Voltou = em outro dia")).toBeTruthy();
    expect(screen.getByText(/-7,0 p\.p\. em relação à oficial/)).toBeTruthy();
    expect(screen.getByText(/é a definição oficial/)).toBeTruthy();
  });
});

describe("semana da cascata", () => {
  it("a principal é 20/11/2023 e 01/05/2023 continua selecionável", async () => {
    const { SEMANAS } = await import("@/components/BlocoSemana");
    expect(SEMANAS[0]).toBe("2023-11-20");
    expect(SEMANAS).toContain("2023-05-01");
  });
});
