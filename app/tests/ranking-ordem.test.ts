import { describe, expect, it } from "vitest";
import { prepararFloresta, type EfeitoApi, type GrupoFator } from "@/lib/floresta";
import { desempenhoRecusa, efeitoComMargem, emVezDe, periodoBase } from "@/lib/painel";

const efeito = (fator: string, grupo: EfeitoApi["grupo"], pp: number, suficiente = true): EfeitoApi => ({
  fator: fator.startsWith("d") ? "tema_descritivo" : fator, nivel: fator, referencia: "y", grupo, n_nivel: 200, n_referencia: 2000, taxa_nivel: 0.2, taxa_referencia: 0.24,
  efeito_bruto_pp: pp, bruto_ic_inf: pp - 4, bruto_ic_sup: pp + 4, efeito_ajustado_pp: pp, ajustado_ic_inf: pp - 4, ajustado_ic_sup: pp + 4,
  p_valor: 0.01, significativo_fdr: true, e_value: 1.5, metodo: "logit_ame", amostra_suficiente: suficiente, leitura: null, ordem: null,
});

describe("ranking da Tela 2 — ordem por tamanho do efeito", () => {
  const GRUPOS: GrupoFator[] = ["assistente", "perfil", "engajamento", "descritivo"];
  const dados = [
    efeito("a1", "assistente", 2), efeito("a2", "assistente", -15), efeito("a3", "assistente", 30, false), efeito("a4", "assistente", 8),
    efeito("p1", "perfil", -3), efeito("p2", "perfil", 12), efeito("p3", "perfil", -25, false), efeito("p4", "perfil", -9),
    efeito("e1", "engajamento", 5), efeito("e2", "engajamento", -20), efeito("e3", "engajamento", 40, false), efeito("e4", "engajamento", 1),
    efeito("d1", "perfil", -7), efeito("d2", "perfil", 18), efeito("d3", "perfil", 50, false), efeito("d4", "perfil", 0.5),
  ];

  for (const g of GRUPOS) {
    it(`aba ${g}: |efeito| decrescente e 'pouca gente' no fim`, () => {
      const { linhas } = prepararFloresta(dados, g);
      expect(linhas.length).toBe(4);
      const firmes = linhas.filter((l) => !l.pequena);
      const pequenas = linhas.filter((l) => l.pequena);
      expect(pequenas.length).toBe(1);
      // a(s) linha(s) de pouca gente vêm depois de todas as demais
      expect(linhas.slice(-pequenas.length).every((l) => l.pequena)).toBe(true);
      const tamanhos = firmes.map((l) => Math.abs((l.ajustado ?? l.bruto)!.efeito));
      expect(tamanhos).toEqual([...tamanhos].sort((a, b) => b - a));
    });
  }
});

describe("textos do ranking", () => {
  it("efeitoComMargem: número com 'a menos/a mais' e margem entre parênteses; sem número para pouca gente", () => {
    const { linhas } = prepararFloresta([efeito("p1", "perfil", -16), efeito("p2", "perfil", 10, false)], "perfil");
    const firme = linhas.find((l) => !l.pequena)!;
    const r = efeitoComMargem(firme)!;
    expect(r.numero).toBe("16 a menos");
    expect(r.margem).toBe("(entre 12 e 20)");
    expect(efeitoComMargem(linhas.find((l) => l.pequena)!)).toBeNull();
  });

  it("emVezDe: diz com o quê compara, e fica vazio quando o nome já diz", () => {
    expect(emVezDe("recusa", "sim", "não")).toBe("em vez de ter respondido");
    expect(emVezDe("modelo_familia", "gpt-4", "gpt-3.5")).toBe("");
    expect(emVezDe("fator_inexistente", "x", "y")).toBe("");
  });

  it("periodoBase: mês/ano por extenso curto", () => {
    expect(periodoBase("2023-04-10", "2024-04-01")).toBe("abr/2023 a abr/2024");
  });

  it("desempenhoRecusa: lê precisão e cobertura da tabela; sem esses campos devolve null", () => {
    const v = [
      { classificador: "recusa", modelo: "regras:1", n: 200, detalhe_json: { por_classe: { sim: { precisao: 0.32, revocacao: 0.8 } } } },
      { classificador: "recusa", modelo: "openrouter:x", n: 200, detalhe_json: { por_classe: { sim: { precisao: 0.5833, revocacao: 0.7 } } } },
    ];
    expect(desempenhoRecusa(v)).toEqual({ precisao: 0.5833, cobertura: 0.7, n: 200 });
    expect(desempenhoRecusa([{ classificador: "recusa", modelo: "openrouter:x", n: 200, detalhe_json: {} }])).toBeNull();
  });
});
