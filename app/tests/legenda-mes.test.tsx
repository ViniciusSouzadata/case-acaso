// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { GraficoTaxa } from "@/components/graficos/GraficoTaxa";
import type { LinhaGrafico } from "@/lib/graficos";

afterEach(cleanup);

const linha = (periodo: string, extra: Partial<LinhaGrafico> = {}): LinhaGrafico => ({
  periodo, rotulo: periodo, taxa: 24, icBase: 20, icAltura: 8, mm4: null, novos: 300, voltaram: 70, icInf: 0.2, icSup: 0.28, taxaFracao: 0.24,
  amostraOk: true, madura: true, inicioColeta: false, ...extra,
});

describe("legenda do gráfico principal mostra só o que está desenhado", () => {
  it("visão Mês (sem média de 4 semanas, sem mês com pouca gente): só 'Quantos voltaram' e 'Margem de erro'", () => {
    render(<GraficoTaxa linhas={[linha("2023-04-01"), linha("2023-05-01"), linha("2023-06-01", { madura: false })]} />);
    const leg = screen.getByRole("list", { name: "Legenda" });
    expect(leg.textContent).toContain("Quantos voltaram");
    expect(leg.textContent).toContain("Margem de erro");
    expect(leg.textContent).not.toContain("Média de 4 semanas");
    expect(leg.textContent).not.toContain("pouca gente");
    expect(screen.queryByText("em andamento")).toBeNull(); // um único período em andamento não tem área para o rótulo
  });

  it("visão Semana: média de 4 semanas e '○ = pouca gente' aparecem quando existem", () => {
    render(<GraficoTaxa linhas={[linha("2023-04-03", { mm4: 23 }), linha("2023-04-10", { mm4: 24, amostraOk: false })]} />);
    const leg = screen.getByRole("list", { name: "Legenda" });
    expect(leg.textContent).toContain("Média de 4 semanas");
    expect(leg.textContent).toContain("○ = pouca gente");
  });
});
