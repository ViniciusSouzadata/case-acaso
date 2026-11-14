// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PaginaFatores from "@/app/fatores/page";
import PaginaRetencao from "@/app/page";
import type { EfeitoApi } from "@/lib/floresta";

// Interações principais das telas em painel: cartão abre o seu detalhe, Esc fecha, clique na semana marcada troca o bloco,
// cartão de achado realça a linha do ranking. Respostas simuladas por rota; só números inventados.
const mock = vi.hoisted(() => ({ respostas: {} as Record<string, unknown>, pedidos: [] as string[] }));
vi.mock("@/lib/useApi", () => ({
  useApi: (url: string) => {
    mock.pedidos.push(url);
    const chave = Object.keys(mock.respostas).find((k) => url.startsWith(k));
    return { estado: "ok", corpo: { dados: chave ? mock.respostas[chave] : [], meta: {} } };
  },
}));
// O gráfico de verdade não renderiza no jsdom (largura 0): o dublê expõe as semanas marcadas como botões e repassa o clique.
vi.mock("@/components/graficos/GraficoTaxa", () => ({
  GraficoTaxa: ({ marcadas = [], onEscolher }: { marcadas?: string[]; onEscolher?: (p: string) => void }) => (
    <div data-testid="grafico">
      {marcadas.map((p) => <button key={p} type="button" data-ponto={p} onClick={() => onEscolher?.(p)}>{`ponto ${p}`}</button>)}
    </div>
  ),
}));
vi.mock("@/components/graficos/Cascata", () => ({ Cascata: () => <div /> }));

afterEach(cleanup);

const coorte = { novos: 80, voltaram_7d: 20, taxa: 0.25, ic_inf: 0.18, ic_sup: 0.34, taxa_mm4: 0.24, madura: true, amostra_suficiente: true, inicio_coleta: false };
const resumoSem = (semana: string, delta: number) => ({ resumo: { semana, base_descricao: "x", n_base: 100, n_semana: 80, taxa_base: 0.26, taxa_semana: 0.2, delta_pp: delta, mix_pp: -0.4, taxa_pp: delta + 0.4, p_valor: 0.3, conclusao: null }, segmentos: [] });
const indicador = (i: string, nome: string) => ({ indicador: i, nome_exibicao: nome, definicao: `definição de ${nome}`, formula: "f", denominador: "d", periodo_referencia: "p", fonte: "fonte", sql_referencia: "", limitacoes: "l" });

describe("Tela 1 — interações", () => {
  beforeEach(() => {
    mock.pedidos = [];
    mock.respostas = {
      "/api/retencao/resumo": { usuarios: 2372, voltaram_7d: 566, taxa: 0.2386, ic_inf: 0.2219, ic_sup: 0.2562 },
      "/api/retencao/coortes": [{ periodo: "2023-05-01", ...coorte }, { periodo: "2023-11-20", ...coorte }],
      "/api/retencao/sensibilidade": [{ definicao: "a", taxa: 0.17 }, { definicao: "b", taxa: 0.25 }],
      "/api/semana/decomposicao?semana=2023-11-20": resumoSem("2023-11-20", -4.9),
      "/api/semana/decomposicao?semana=2023-05-01": resumoSem("2023-05-01", -7.7),
      "/api/dicionario": [indicador("taxa_retorno_7d", "Taxa de retorno em 7 dias")],
    };
  });

  it("cada cartão de número é um botão que abre o seu detalhe, e Esc fecha", () => {
    render(<PaginaRetencao />);
    for (const nome of [/Voltam em até 7 dias/, /Pessoas novas/, /^Voltaram/, /Se mudar a forma de contar/]) {
      fireEvent.click(screen.getAllByRole("button", { name: nome })[0]!);
      expect(screen.getByRole("dialog")).toBeTruthy();
      fireEvent.keyDown(window, { key: "Escape" });
      expect(screen.queryByRole("dialog")).toBeNull();
    }
  });

  it("o cartão da taxa abre a definição do dicionário em linguagem comum", () => {
    render(<PaginaRetencao />);
    fireEvent.click(screen.getAllByRole("button", { name: /Voltam em até 7 dias/ })[0]!);
    expect(mock.pedidos).toContain("/api/dicionario?indicador=taxa_retorno_7d");
    expect(within(screen.getByRole("dialog")).getByTestId("detalhe-indicador").textContent).toContain("definição de Taxa de retorno em 7 dias");
  });

  it("clicar na semana marcada troca o bloco 'O que houve em …'", () => {
    render(<PaginaRetencao />);
    expect(screen.getByRole("heading", { name: /O que houve em 20\/11\/2023/ })).toBeTruthy();
    fireEvent.click(screen.getByText("ponto 2023-05-01"));
    expect(screen.getByRole("heading", { name: /O que houve em 01\/05\/2023/ })).toBeTruthy();
    expect(mock.pedidos).toContain("/api/semana/decomposicao?semana=2023-05-01");
    expect(screen.getByTestId("conclusao-semana").textContent).toContain("voltaram menos");
  });

  it("no gráfico por mês nenhuma semana fica marcada; o controle Semana | Mês existe", () => {
    render(<PaginaRetencao />);
    expect(screen.getAllByText(/^ponto /).length).toBe(2);
    fireEvent.click(screen.getByRole("button", { name: "Mês" }));
    expect(mock.pedidos).toContain("/api/retencao/coortes?granularidade=mes");
    expect(screen.queryAllByText(/^ponto /).length).toBe(0);
  });
});

describe("Tela 2 — cartão do achado realça a linha do ranking", () => {
  const efeito = (fator: string, nivel: string, grupo: EfeitoApi["grupo"], pp: number): EfeitoApi => ({
    fator, nivel, referencia: "x", grupo, n_nivel: 200, n_referencia: 2000, taxa_nivel: 0.2, taxa_referencia: 0.24,
    efeito_bruto_pp: pp, bruto_ic_inf: pp - 4, bruto_ic_sup: pp + 4, efeito_ajustado_pp: pp, ajustado_ic_inf: pp - 4, ajustado_ic_sup: pp + 4,
    p_valor: 0.01, significativo_fdr: fator === "recusa", e_value: 1.5, metodo: "logit_ame", amostra_suficiente: true, leitura: null, ordem: 1,
  });
  const achado = (ordem: number) => ({ ordem, titulo: `achado ${ordem}`, evidencia: "e", decisao: "d", limite: "l", numero_destaque: "−1", rotulo_destaque: "a cada 100", acao_curta: "Fazer algo." });

  beforeEach(() => {
    // gpt-4 fica no grupo "perfil" de propósito: o realce tem de trocar de aba
    mock.respostas = {
      "/api/fatores/efeitos": [efeito("recusa", "sim", "assistente", -16), efeito("modelo_familia", "gpt-4", "perfil", -3)],
      "/api/achados": [achado(1), achado(2), achado(3)],
    };
  });

  const realcadas = () => [...document.querySelectorAll("[data-realce]")].map((e) => `${e.getAttribute("data-fator")}|${e.getAttribute("data-nivel")}`);

  it("achado 1 realça 'Recebeu recusa'; sair do cartão tira o realce", () => {
    render(<PaginaFatores />);
    expect(realcadas()).toEqual([]);
    fireEvent.mouseEnter(document.querySelector("[data-achado='1']")!);
    expect(realcadas()).toEqual(["recusa|sim"]);
    fireEvent.mouseLeave(document.querySelector("[data-achado='1']")!);
    expect(realcadas()).toEqual([]);
  });

  it("achado 2 realça o GPT-4 e troca de aba quando ele está em outro grupo", () => {
    render(<PaginaFatores />);
    expect(document.querySelector("[data-fator='modelo_familia']")).toBeNull(); // a aba Assistente não o mostra
    fireEvent.mouseEnter(document.querySelector("[data-achado='2']")!);
    expect(screen.getByRole("tab", { name: /Quem é a pessoa/ }).getAttribute("aria-selected")).toBe("true");
    expect(realcadas()).toEqual(["modelo_familia|gpt-4"]);
  });

  it("o achado 3 (semanas) não realça nenhuma linha", () => {
    render(<PaginaFatores />);
    fireEvent.mouseEnter(document.querySelector("[data-achado='3']")!);
    expect(realcadas()).toEqual([]);
  });

  it("clicar na linha do ranking abre o detalhe e Esc fecha", () => {
    render(<PaginaFatores />);
    fireEvent.click(document.querySelector("[data-fator='recusa'] button")!);
    expect(screen.getByRole("dialog")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
