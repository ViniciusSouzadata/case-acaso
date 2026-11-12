// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { DicaCoorte } from "@/components/graficos/DicaCoorte";
import { TabelaCoortes } from "@/components/graficos/TabelaCoortes";
import {
  faixasEras,
  faixasImaturas,
  prepararCoortes,
  resumoVariacao,
  rotuloPeriodo,
  type CoorteApi,
  type EraApi,
} from "@/lib/graficos";

afterEach(cleanup);

const base = { voltaram_7d: 20, taxa: 0.25, ic_inf: 0.18, ic_sup: 0.34, taxa_mm4: 0.24, madura: true, amostra_suficiente: true, inicio_coleta: false };
const coortes: CoorteApi[] = [
  { periodo: "2023-04-24", novos: 70, ...base },
  { periodo: "2023-05-01", novos: 84, ...base, taxa: 0.1667, voltaram_7d: 14 },
  { periodo: "2023-05-08", novos: 12, ...base, taxa: 0.5, voltaram_7d: 6, ic_inf: 0.25, ic_sup: 0.75, amostra_suficiente: false },
  { periodo: "2024-04-08", novos: 20, voltaram_7d: null, taxa: null, ic_inf: null, ic_sup: null, taxa_mm4: null, madura: false, amostra_suficiente: false, inicio_coleta: false },
  { periodo: "2024-04-15", novos: 5, voltaram_7d: null, taxa: null, ic_inf: null, ic_sup: null, taxa_mm4: null, madura: false, amostra_suficiente: false, inicio_coleta: false },
];
const eras: EraApi[] = [
  { era: "A", inicio: "2023-04-01", fim: "2023-04-30", descricao: "era A" },
  { era: "B", inicio: "2023-05-01", fim: null, descricao: "era B" },
];

describe("preparação dos dados do gráfico", () => {
  const linhas = prepararCoortes(coortes, "semana");

  it("taxa em %, faixa de incerteza como base + altura; imatura sem ponto", () => {
    expect(linhas[0]!.taxa).toBeCloseTo(25);
    expect(linhas[0]!.icBase).toBeCloseTo(18);
    expect(linhas[0]!.icAltura).toBeCloseTo(16);
    expect(linhas[3]!.taxa).toBeNull();
    expect(linhas[3]!.icAltura).toBeNull();
  });

  it("amostra pequena mantém a taxa (a tela decide como mostrar)", () => {
    expect(linhas[2]!.taxa).toBeCloseTo(50);
    expect(linhas[2]!.amostraOk).toBe(false);
  });

  it("faixas de era são contíguas: cada uma vai até o início da próxima; a última, até o fim", () => {
    const f = faixasEras(linhas, eras);
    expect(f.map((x) => [x.era, x.x1, x.x2])).toEqual([
      ["A", "2023-04-24", "2023-05-01"],
      ["B", "2023-05-01", "2024-04-15"],
    ]);
  });

  it("trechos imaturos consecutivos viram uma só faixa", () => {
    expect(faixasImaturas(linhas)).toEqual([{ x1: "2024-04-08", x2: "2024-04-15" }]);
  });

  it("variação ignora amostra pequena e coorte imatura", () => {
    const v = resumoVariacao(linhas)!;
    expect(v.min).toBeCloseTo(0.1667);
    expect(v.max).toBeCloseTo(0.25);
    expect(v.validas).toBe(2);
  });

  it("rótulos de período", () => {
    expect(rotuloPeriodo("2023-05-01", "semana")).toBe("01/05/23");
    expect(rotuloPeriodo("2023-05-01", "mes")).toBe("mai/23");
  });
});

describe("tabela da Tela 1", () => {
  it("semana com amostra_suficiente=false exibe 'amostra pequena (n = X)' e não a taxa", () => {
    render(<TabelaCoortes linhas={prepararCoortes(coortes, "semana")} unidade="x" />);
    const linha = document.querySelector('[data-periodo="2023-05-08"]') as HTMLElement;
    expect(within(linha).getByText("amostra pequena (n = 12)")).toBeTruthy();
    expect(within(linha).queryByText(/50,0%/)).toBeNull();
  });

  it("semana imatura exibe o rótulo 'ainda dentro dos 7 dias' (nunca como queda)", () => {
    render(<TabelaCoortes linhas={prepararCoortes(coortes, "semana")} unidade="x" />);
    const linha = document.querySelector('[data-periodo="2024-04-08"]') as HTMLElement;
    expect(within(linha).getByText("ainda dentro dos 7 dias")).toBeTruthy();
  });

  it("semana normal mostra taxa e intervalo", () => {
    render(<TabelaCoortes linhas={prepararCoortes(coortes, "semana")} unidade="x" />);
    const linha = document.querySelector('[data-periodo="2023-05-01"]') as HTMLElement;
    expect(within(linha).getByText("16,7%")).toBeTruthy();
    expect(within(linha).getAllByRole("cell").length).toBe(4);
  });

  it("tem legenda e cabeçalhos de coluna (acessibilidade)", () => {
    render(<TabelaCoortes linhas={prepararCoortes(coortes, "semana")} unidade="uma linha por semana" />);
    expect(screen.getByRole("table").querySelector("caption")?.textContent).toContain("uma linha por semana");
    expect(screen.getAllByRole("columnheader").length).toBe(5);
  });
});

describe("dica do ponto", () => {
  const linhas = prepararCoortes(coortes, "semana");
  it("amostra pequena: a dica explica", () => {
    render(<DicaCoorte linha={linhas[2]!} />);
    expect(screen.getByText(/amostra pequena \(n = 12\)/)).toBeTruthy();
    expect(screen.getByText(/poucas pessoas/)).toBeTruthy();
  });
  it("imatura: a dica diz que ainda não é uma queda", () => {
    render(<DicaCoorte linha={linhas[3]!} />);
    expect(screen.getByText(/não é uma queda/)).toBeTruthy();
  });
});

describe("início da coleta", () => {
  const inicio = [{ periodo: "2023-04-17", novos: 60, ...base, taxa: 0.31, inicio_coleta: true }];

  it("tabela mostra a taxa com o aviso de início da coleta; semanas comuns não têm o aviso", () => {
    render(<TabelaCoortes linhas={prepararCoortes([...inicio, ...coortes], "semana")} unidade="x" />);
    const linha = document.querySelector('[data-periodo="2023-04-17"]') as HTMLElement;
    expect(within(linha).getByText("31,0%")).toBeTruthy();
    expect(within(linha).getByText(/Início da coleta: pode incluir usuários antigos, então a taxa tende a sair mais alta/)).toBeTruthy();
    const comum = document.querySelector('[data-periodo="2023-05-01"]') as HTMLElement;
    expect(within(comum).queryByText(/Início da coleta/)).toBeNull();
  });

  it("a dica do ponto traz o aviso", () => {
    const [l] = prepararCoortes(inicio, "semana");
    render(<DicaCoorte linha={l!} />);
    expect(screen.getByText(/Início da coleta/)).toBeTruthy();
    expect(l!.inicioColeta).toBe(true);
  });

  it("o contrato exige o campo inicio_coleta em cada coorte", async () => {
    const { respostaCoortes } = await import("@/lib/esquemas");
    const { readFileSync } = await import("node:fs");
    const { resolve } = await import("node:path");
    const ex = JSON.parse(readFileSync(resolve(process.cwd(), "exemplos/retencao-coortes.json"), "utf-8"));
    expect(respostaCoortes.safeParse(ex).success).toBe(true);
    delete ex.dados[0].inicio_coleta;
    expect(respostaCoortes.safeParse(ex).success).toBe(false);
  });
});
