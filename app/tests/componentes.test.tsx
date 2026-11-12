// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AvisoAmostra } from "@/components/AvisoAmostra";
import { Estado } from "@/components/Estado";
import { Numero } from "@/components/Numero";
import { todasAsMensagens } from "@/lib/mensagens";
import { cruzaZero, formatarPP, formatarPct } from "@/lib/regras";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("regras de confiança (lib/regras)", () => {
  it("cruzaZero: IC que inclui o zero", () => {
    expect(cruzaZero(-1, 2)).toBe(true);
    expect(cruzaZero(0, 2)).toBe(true);
    expect(cruzaZero(0.5, 2)).toBe(false);
    expect(cruzaZero(-3, -0.1)).toBe(false);
    expect(cruzaZero(null, 2)).toBe(false);
  });
  it("formatação em pt-BR", () => {
    expect(formatarPct(0.2386)).toBe("23,9%");
    expect(formatarPP(4.9)).toBe("+4,9 p.p.");
    expect(formatarPP(-2.25)).toBe("-2,3 p.p.");
  });
});

describe("Numero", () => {
  it("normal: valor, intervalo, n e o ícone i", () => {
    render(<Numero rotulo="Taxa de retorno" valor={0.2386} formato="pct" icInf={0.2219} icSup={0.2562} n={2372} indicador="taxa_retorno_7d" />);
    expect(screen.getByTestId("valor").textContent).toBe("23,9%");
    expect(screen.getByText(/intervalo de 95%: 22,2% a 25,6%/)).toBeTruthy();
    expect(screen.getByText("n = 2.372")).toBeTruthy();
    expect(screen.getByRole("button", { name: /O que é este número/ })).toBeTruthy();
    expect(screen.queryByRole("note")).toBeNull();
  });

  it("amostra pequena: o destaque vira 'amostra pequena (n = X)', sem mostrar a taxa, e o aviso aparece", () => {
    render(<Numero rotulo="Taxa" valor={0.1667} formato="pct" icInf={0.06} icSup={0.4} n={12} amostraSuficiente={false} />);
    expect(screen.getByTestId("valor").textContent).toBe("amostra pequena (n = 12)");
    expect(screen.queryByText(/16,7%/)).toBeNull();
    expect(screen.getByRole("note").textContent).toMatch(/poucas pessoas/);
  });

  it("coorte imatura: rótulo 'ainda dentro dos 7 dias', nunca um valor", () => {
    render(<Numero rotulo="Taxa" valor={0.05} formato="pct" n={20} madura={false} />);
    expect(screen.getByTestId("valor").textContent).toBe("ainda dentro dos 7 dias");
    expect(screen.queryByText(/5,0%/)).toBeNull();
  });

  it("efeito com intervalo cruzando o zero recebe o rótulo", () => {
    render(<Numero rotulo="Efeito" valor={1.2} formato="pp" icInf={-2} icSup={4} n={300} />);
    expect(screen.getByText(/não dá para distinguir de zero/)).toBeTruthy();
  });

  it("efeito com intervalo acima de zero não recebe o rótulo", () => {
    render(<Numero rotulo="Efeito" valor={5} formato="pp" icInf={2} icSup={8} n={300} />);
    expect(screen.queryByText(/não dá para distinguir de zero/)).toBeNull();
  });
});

describe("AvisoAmostra e Estado", () => {
  it("o aviso traz o n", () => {
    render(<AvisoAmostra n={7} />);
    expect(screen.getByRole("note").textContent).toContain("n = 7");
  });
  it("erro mostra o request_id", () => {
    render(<Estado tipo="erro" mensagem="país ainda não carregado" requestId="req_ab12cd" />);
    expect(screen.getByRole("alert").textContent).toContain("req_ab12cd");
    expect(screen.getByRole("alert").textContent).toContain("país ainda não carregado");
  });
  it("carregando e vazio", () => {
    render(<Estado tipo="carregando" />);
    expect(screen.getByRole("status").textContent).toMatch(/Carregando/);
    cleanup();
    render(<Estado tipo="vazio" />);
    expect(screen.getByRole("status").textContent).toMatch(/Ainda não há dados/);
  });
});

describe("Glossario (abre pelo ícone i)", () => {
  const item = {
    indicador: "taxa_retorno_7d",
    nome_exibicao: "Taxa de retorno em 7 dias",
    definicao: "De cada 100 pessoas, quantas voltaram.",
    formula: "voltaram_7d / novos_usuarios",
    denominador: "Usuários elegíveis.",
    periodo_referencia: "Semana da 1ª sessão.",
    fonte: "mart.agg_retencao_periodo",
    sql_referencia: "SELECT taxa FROM mart.agg_retencao_periodo",
    limitacoes: "Depende da chave de usuário.",
  };

  it("busca em /api/dicionario e mostra definição, fórmula, denominador, período, fonte e SQL; Esc fecha", async () => {
    const fetchSimulado = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ dados: [item], meta: { request_id: "req_1" } }),
    }));
    vi.stubGlobal("fetch", fetchSimulado);
    render(<Numero rotulo="Taxa" valor={0.24} formato="pct" icInf={0.2} icSup={0.3} n={100} indicador="taxa_retorno_7d" />);
    fireEvent.click(screen.getByRole("button", { name: /O que é este número/ }));
    await waitFor(() => expect(screen.getByText(item.definicao)).toBeTruthy());
    expect(fetchSimulado).toHaveBeenCalledWith("/api/dicionario?indicador=taxa_retorno_7d");
    for (const texto of [item.formula, item.denominador, item.periodo_referencia, item.fonte, item.sql_referencia, item.limitacoes]) {
      expect(screen.getByText(texto)).toBeTruthy();
    }
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("erro da API aparece com o request_id", async () => {
    vi.stubGlobal("fetch", async () => ({
      ok: false,
      status: 500,
      json: async () => ({ erro: { codigo: "ERRO_INTERNO", mensagem: "Erro interno", request_id: "req_zz" } }),
    }));
    render(<Numero rotulo="Taxa" valor={0.24} formato="pct" n={100} indicador="x" />);
    fireEvent.click(screen.getByRole("button", { name: /O que é este número/ }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("req_zz"));
  });
});

describe("mensagens (REQ-409: linguagem simples)", () => {
  it("nenhum texto do arquivo usa termo técnico proibido", () => {
    const todos: string[] = [];
    const percorrer = (n: unknown) => {
      if (typeof n === "string") todos.push(n);
      else if (n && typeof n === "object") Object.values(n).forEach(percorrer);
    };
    percorrer(todasAsMensagens);
    expect(todos.length).toBeGreaterThan(10);
    for (const s of todos) expect(s).not.toMatch(/regress[ãa]o|propens[ãa]o|p-valor|p valor/i);
  });
});
