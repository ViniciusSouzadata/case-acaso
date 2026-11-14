// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Floresta } from "@/components/graficos/Floresta";
import { contarDistinguiveis, contarDoGrupo, fraseResposta, prepararFloresta, type EfeitoApi } from "@/lib/floresta";

afterEach(cleanup);

const base: EfeitoApi = {
  fator: "recusa", nivel: "sim", referencia: "não", grupo: "assistente", n_nivel: 200, n_referencia: 2000,
  taxa_nivel: 0.2, taxa_referencia: 0.24,
  efeito_bruto_pp: -4, bruto_ic_inf: -9, bruto_ic_sup: 1,
  efeito_ajustado_pp: -6, ajustado_ic_inf: -10, ajustado_ic_sup: -2,
  p_valor: 0.004, significativo_fdr: true, e_value: 1.5, metodo: "logit_ame", amostra_suficiente: true,
  leitura: "recusa: 'sim' voltou 6,0 p.p. menos do que 'não'", ordem: 1,
};
const cruza: EfeitoApi = { ...base, fator: "modelo_familia", nivel: "gpt-4", referencia: "gpt-3.5", efeito_ajustado_pp: 1, ajustado_ic_inf: -3, ajustado_ic_sup: 5, p_valor: 0.6, significativo_fdr: false, leitura: "modelo: 'gpt-4' contra 'gpt-3.5' não dá para distinguir de zero" };
const pequeno: EfeitoApi = { ...base, fator: "idioma", grupo: "perfil", nivel: "outros", n_nivel: 12, amostra_suficiente: false, efeito_ajustado_pp: null, ajustado_ic_inf: null, ajustado_ic_sup: null, significativo_fdr: null, leitura: "idioma da pergunta: 'outros' tem poucos usuários (n=12)" };
const engaj: EfeitoApi = { ...base, fator: "n_turnos_sessao", grupo: "engajamento", nivel: "4 ou mais", referencia: "1", efeito_bruto_pp: 15, bruto_ic_inf: 10, bruto_ic_sup: 20, efeito_ajustado_pp: 9, ajustado_ic_inf: 4, ajustado_ic_sup: 14, leitura: "turnos na visita: '4 ou mais' voltou 15,0 p.p. mais" };

describe("preparação da floresta", () => {
  it("ordena pelo tamanho do efeito (ajustado se houver)", () => {
    const pouco = { ...base, fator: "dispositivo", efeito_ajustado_pp: 0.5, ajustado_ic_inf: -1, ajustado_ic_sup: 2 };
    const { linhas } = prepararFloresta([pouco, base, cruza], "assistente");
    // |efeito ajustado|: recusa 6, modelo 1, dispositivo 0,5
    expect(linhas.map((l) => l.fator)).toEqual(["recusa", "modelo_familia", "dispositivo"]);
  });

  it("a escala é simétrica em torno do zero (zero no meio) e cobre todos os intervalos", () => {
    const { linhas, limite } = prepararFloresta([base, cruza], "assistente");
    for (const l of linhas) {
      expect(l.pos.zero).toBeCloseTo(50);
      for (const p of [l.pos.bruto, l.pos.ajustado]) {
        if (!p) continue;
        expect(p[0]).toBeGreaterThanOrEqual(0);
        expect(p[2]).toBeLessThanOrEqual(100);
      }
    }
    expect(limite).toBeGreaterThan(10);
  });

  it("só traz o grupo pedido", () => {
    expect(prepararFloresta([base, pequeno, engaj], "perfil").linhas.map((l) => l.fator)).toEqual(["idioma"]);
  });

  it("engajamento nunca tem ajustado, mesmo que a API traga", () => {
    const [l] = prepararFloresta([engaj], "engajamento").linhas;
    expect(l!.ajustado).toBeNull();
    expect(l!.bruto).not.toBeNull();
  });

  it("IC cruzando zero = não distingue; amostra pequena não entra na conta", () => {
    const { linhas } = prepararFloresta([base, cruza, pequeno], "assistente");
    expect(linhas.find((l) => l.fator === "modelo_familia")!.naoDistingue).toBe(true);
    expect(linhas.find((l) => l.fator === "recusa")!.naoDistingue).toBe(false);
    const p = prepararFloresta([pequeno], "perfil").linhas[0]!;
    expect(p.pequena).toBe(true);
    expect(p.naoDistingue).toBe(false);
  });

  it("contagens do título e da frase-resposta", () => {
    expect(contarDistinguiveis([base, cruza, pequeno, engaj])).toEqual({ k: 1, m: 2, f: 1 });
    // 1 fora do zero, mas sem resistir à correção: conta em k e não em f
    expect(contarDistinguiveis([{ ...base, significativo_fdr: false }])).toEqual({ k: 1, m: 1, f: 0 });
    expect(contarDoGrupo(prepararFloresta([base, cruza], "assistente").linhas)).toEqual({ k: 1, m: 2 });
  });
});

describe("componente Floresta", () => {
  const renderGrupo = (efeitos: EfeitoApi[], g: "assistente" | "perfil" | "engajamento") => {
    const { linhas, limite } = prepararFloresta(efeitos, g);
    return render(<Floresta linhas={linhas} limite={limite} />);
  };
  const linhaDe = (fator: string) => document.querySelector(`[data-fator="${fator}"]`) as HTMLElement;

  it("efeito com IC cruzando o zero recebe o rótulo 'sem diferença clara'", () => {
    renderGrupo([base, cruza], "assistente");
    expect(within(linhaDe("modelo_familia")).getByText("sem diferença clara")).toBeTruthy();
    expect(within(linhaDe("recusa")).queryByText("sem diferença clara")).toBeNull();
  });

  it("efeito distinguível mostra a marca de que resiste à correção para muitos testes", () => {
    renderGrupo([base], "assistente");
    expect(within(linhaDe("recusa")).getByText(/continua diferente de zero/)).toBeTruthy();
  });

  it("IC fora do zero sem resistir à correção recebe o rótulo 'pode ser acaso'", () => {
    renderGrupo([{ ...base, significativo_fdr: false }], "assistente");
    expect(within(linhaDe("recusa")).getByText(/pode ser acaso/)).toBeTruthy();
    expect(within(linhaDe("recusa")).queryByText(/continua diferente de zero/)).toBeNull();
  });

  it("mostra bruto e ajustado, a frase de leitura e o n", () => {
    renderGrupo([base], "assistente");
    const l = linhaDe("recusa");
    expect(l.querySelector('[data-ponto="bruto"]')).not.toBeNull();
    expect(l.querySelector('[data-ponto="ajustado"]')).not.toBeNull();
    expect(within(l).getByText(/voltou 6,0 p\.p\. menos/)).toBeTruthy();
    expect(within(l).getByText(/Diferença direta/)).toBeTruthy();
    expect(within(l).getByText(/Entre pessoas parecidas/)).toBeTruthy();
  });

  it("engajamento não mostra o ponto nem o texto de ajustado", () => {
    renderGrupo([engaj], "engajamento");
    const l = linhaDe("n_turnos_sessao");
    expect(l.querySelector('[data-ponto="ajustado"]')).toBeNull();
    expect(l.querySelector('[data-ponto="bruto"]')).not.toBeNull();
    expect(within(l).queryByText(/Entre pessoas parecidas/)).toBeNull();
    expect(within(l).getByText(/sem comparar pessoas parecidas/)).toBeTruthy();
  });

  it("amostra pequena: aviso com o n, sem números em destaque", () => {
    renderGrupo([pequeno], "perfil");
    const l = linhaDe("idioma");
    expect(within(l).getByRole("note").textContent).toContain("pouca gente (12 pessoas)");
    expect(within(l).queryByText(/Diferença direta/)).toBeNull();
    expect(within(l).queryByText("sem diferença clara")).toBeNull();
  });

  it("o texto principal não usa termo técnico proibido", () => {
    renderGrupo([base, cruza, pequeno], "assistente");
    expect(document.body.textContent).not.toMatch(/regress[ãa]o|propens[ãa]o|p-valor/i);
    expect(screen.getAllByRole("listitem").length).toBeGreaterThan(0);
  });
});

describe("tema descritivo (grupo à parte)", () => {
  const desc: EfeitoApi = { ...base, fator: "tema_descritivo", grupo: "perfil", nivel: "trabalho/negócios", referencia: "demais temas", efeito_bruto_pp: 9, bruto_ic_inf: 3, bruto_ic_sup: 15, efeito_ajustado_pp: null, ajustado_ic_inf: null, ajustado_ic_sup: null, significativo_fdr: null, leitura: null };

  it("não aparece no Perfil nem entra nas contagens da frase-resposta", () => {
    expect(prepararFloresta([base, desc], "perfil").linhas).toEqual([]);
    expect(prepararFloresta([base, desc], "descritivo").linhas.map((l) => l.fator)).toEqual(["tema_descritivo"]);
    expect(contarDistinguiveis([base, desc])).toEqual({ k: 1, m: 1, f: 1 });
  });

  it("mostra só o bruto, sem ajuste e sem rótulo de acaso", () => {
    const { linhas, limite } = prepararFloresta([desc], "descritivo");
    render(<Floresta linhas={linhas} limite={limite} />);
    const l = document.querySelector('[data-fator="tema_descritivo"]') as HTMLElement;
    expect(l.querySelector('[data-ponto="ajustado"]')).toBeNull();
    expect(within(l).getByText(/sem comparar pessoas parecidas/)).toBeTruthy();
    expect(within(l).queryByText(/pode ser acaso/)).toBeNull();
  });
});

describe("frase-resposta: concordância", () => {
  it("singular quando é 1 (k = 1 e f = 1)", () => {
    const frase = fraseResposta(1, 27, 1);
    expect(frase).toContain("1 tem margem de erro");
    expect(frase).toContain("1 continua diferente de zero");
    expect(frase).not.toMatch(/1 têm|1 continuam/);
  });

  it("plural quando é mais de 1 (k > 1 e f > 1)", () => {
    const frase = fraseResposta(5, 27, 3);
    expect(frase).toContain("5 têm margem de erro");
    expect(frase).toContain("3 continuam diferentes de zero");
    expect(frase).toContain("27 comparações");
  });

  it("mistura: k plural com f singular, e o caso f = 0 (nenhuma continua)", () => {
    expect(fraseResposta(5, 27, 1)).toMatch(/5 têm .* 1 continua diferente de zero/);
    expect(fraseResposta(1, 27, 0)).toMatch(/1 tem margem de erro.*nenhuma continua diferente de zero/);
    expect(fraseResposta(0, 0, 0)).toBe("Ainda não há comparações para mostrar.");
  });
});
