// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DetalheFator } from "@/components/DetalheFator";
import { nomeCovariavel } from "@/components/DetalheBalanco";
import { Dicionario, nomeConferencia } from "@/components/DetalheQualidade";
import { prepararFloresta, type EfeitoApi } from "@/lib/floresta";
import { faixaCem, fraseResultado, fraseVeredito, nomeCurto } from "@/lib/painel";

// Pedido 13 — painéis de clique curtos: número/gráfico, até 3 frases e o resto no bloco técnico.
const base: EfeitoApi = {
  fator: "recusa", nivel: "sim", referencia: "não", grupo: "assistente", n_nivel: 132, n_referencia: 2240, taxa_nivel: 0.098485, taxa_referencia: 0.246875,
  efeito_bruto_pp: -14.839, bruto_ic_inf: -19.2391, bruto_ic_sup: -8.3284, efeito_ajustado_pp: -16.41, ajustado_ic_inf: -21.3513, ajustado_ic_sup: -11.4688,
  p_valor: 0, significativo_fdr: true, e_value: 5.3, metodo: "logit_ame", amostra_suficiente: true, leitura: "texto de máquina que não deve aparecer", ordem: 1,
};
const linha = (e: Partial<EfeitoApi>, grupo: "assistente" | "perfil" | "engajamento" | "descritivo" = (e.grupo as "assistente") ?? "assistente") => prepararFloresta([{ ...base, ...e }], grupo).linhas[0]!;

// texto visível: tudo menos o conteúdo dos blocos técnicos recolhidos
const visivel = (el: Element) => {
  const c = el.cloneNode(true) as Element;
  c.querySelectorAll("details").forEach((d) => d.remove());
  return c.textContent ?? "";
};
const PROIBIDAS = /\bIP\b|elegível|elegíveis|sessão|coorte|UTC|BDR-|p\.p\.|intervalo|ajust|anômal|tráfego|propensão|::|_|Spanish|Portuguese|English/i;

afterEach(cleanup);

describe("frases do detalhe de uma linha do ranking", () => {
  it("faixa em pessoas a cada 100, com o sinal certo", () => {
    expect(faixaCem(-21.35, -11.47, true)).toBe("entre 11 e 21 a menos");
    expect(faixaCem(14, 28, false)).toBe("entre 14 e 28");
    expect(faixaCem(-8.3, 2.5, true)).toBe("entre 8,3 a menos e 2,5 a mais");
  });

  it("recusa: resultado entre pessoas parecidas e veredito 'diferença real'", () => {
    const l = linha({});
    expect(fraseResultado(l)).toBe("Entre pessoas parecidas, voltam 16 a menos a cada 100 (entre 11 e 21 a menos).");
    expect(fraseVeredito(l)).toMatch(/^É uma diferença real/);
  });

  it("aba só descritiva usa a diferença direta e diz que só descreve", () => {
    const l = linha({ fator: "n_turnos_sessao", nivel: "4 ou mais", referencia: "1", grupo: "engajamento", efeito_bruto_pp: 21, bruto_ic_inf: 14, bruto_ic_sup: 28, efeito_ajustado_pp: null, ajustado_ic_inf: null, ajustado_ic_sup: null });
    expect(fraseResultado(l)).toBe("Voltam 21 a mais a cada 100 (entre 14 e 28).");
    expect(fraseVeredito(l)).toMatch(/^Só descreve/);
  });

  it("assunto: nome sem prefixo e veredito sem a frase errada sobre 'depois da primeira resposta'", () => {
    expect(nomeCurto("tema_descritivo", "estudo/dever de casa")).toBe("Estudo");
    const l = linha({ fator: "tema_descritivo", nivel: "estudo/dever de casa", referencia: "demais temas", grupo: "perfil" }, "descritivo");
    expect(fraseVeredito(l)).toMatch(/aqui não comparamos pessoas parecidas/);
    expect(fraseVeredito(l)).not.toMatch(/depois da primeira resposta/);
  });
});

describe("DetalheFator", () => {
  it("abre com duas barras, duas frases e o técnico recolhido; sem texto de máquina nem termo proibido", () => {
    const { container } = render(<DetalheFator l={linha({})} />);
    const barras = screen.getByTestId("duas-barras").textContent ?? "";
    expect(barras).toContain("Com recusa: 10 de cada 100 voltaram");
    expect(barras).toContain("Sem recusa: 25 de cada 100 voltaram");
    expect(barras).toContain("132 pessoas");
    const texto = visivel(container);
    expect(texto).not.toMatch(PROIBIDAS);
    expect(texto).not.toMatch(/texto de máquina/);
    expect(texto.trim().split(/\s+/).length).toBeLessThanOrEqual(70);
    expect(container.querySelector("details")).not.toBeNull();
  });

  it("pouca gente: sem barras e com a frase de amostra pequena", () => {
    const { container } = render(<DetalheFator l={linha({ fator: "dispositivo", nivel: "outro", referencia: "computador", n_nivel: 11, amostra_suficiente: false, efeito_ajustado_pp: null, ajustado_ic_inf: null, ajustado_ic_sup: null })} />);
    expect(screen.queryByTestId("duas-barras")).toBeNull();
    expect(visivel(container)).toMatch(/Só 11 pessoas neste grupo/);
  });
});

describe("nomes legíveis", () => {
  it("conferências e características do balanço", () => {
    expect(nomeConferencia("elegiveis")).toBe("Pessoas que entram na conta");
    expect(nomeConferencia("semanas_com_voltaram_divergentes")).toBe("Semanas em que a contagem de voltas não bate");
    expect(nomeCovariavel("idioma::English")).toBe("idioma da pergunta: inglês");
    expect(nomeCovariavel("faixa_chars_pergunta::101–400")).not.toMatch(/::|_/);
  });
});

describe("dicionário dos números", () => {
  it("só um termo fica aberto por vez", () => {
    vi.stubGlobal("fetch", async () => new Response(JSON.stringify({ dados: [
      { indicador: "a", nome_exibicao: "Termo A", definicao: "Definição de A.", formula: "f", denominador: "d", periodo_referencia: "p", fonte: "s", sql_referencia: "select 1", limitacoes: "l" },
      { indicador: "b", nome_exibicao: "Termo B", definicao: "Definição de B.", formula: "f", denominador: "d", periodo_referencia: "p", fonte: "s", sql_referencia: "select 2", limitacoes: "l" },
    ], meta: {} }), { status: 200 }));
    return (async () => {
      render(<Dicionario />);
      fireEvent.click(await screen.findByRole("button", { name: /Termo A/ }));
      expect(screen.getByText("Definição de A.")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: /Termo B/ }));
      expect(screen.queryByText("Definição de A.")).toBeNull();
      expect(screen.getByText("Definição de B.")).toBeTruthy();
      vi.unstubAllGlobals();
    })();
  });
});
