// @vitest-environment jsdom
// Rodada de clareza (T-406): uma linha por fator, títulos em frase, cartões resumidos, termos técnicos fora do texto principal.
import { cleanup, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Floresta, tituloLinha } from "@/components/graficos/Floresta";
import { resumir } from "@/lib/achados";
import { contarDistinguiveis, contarDoGrupo, prepararFloresta, type EfeitoApi } from "@/lib/floresta";
import { t, todasAsMensagens } from "@/lib/mensagens";
import { tipoClassificador, traduzirTermos } from "@/lib/qualidade";

afterEach(cleanup);

const base: EfeitoApi = {
  fator: "recusa", nivel: "sim", referencia: "não", grupo: "assistente", n_nivel: 132, n_referencia: 2240,
  taxa_nivel: 0.1, taxa_referencia: 0.25, efeito_bruto_pp: -14.8, bruto_ic_inf: -19.2, bruto_ic_sup: -8.3,
  efeito_ajustado_pp: -16.4, ajustado_ic_inf: -21.4, ajustado_ic_sup: -11.5, p_valor: 0.001, significativo_fdr: true,
  e_value: 5.3, metodo: "logit_ame", amostra_suficiente: true, leitura: "leitura do ajuste", ordem: 1,
};
const ipwSem: EfeitoApi = { ...base, metodo: "ipw", efeito_ajustado_pp: null, ajustado_ic_inf: null, ajustado_ic_sup: null, significativo_fdr: null, leitura: "grupos não comparáveis" };
const modelo: EfeitoApi = { ...base, fator: "modelo_familia", nivel: "gpt-4", referencia: "gpt-3.5", n_nivel: 1032, n_referencia: 1340, efeito_ajustado_pp: -2.9, ajustado_ic_inf: -8, ajustado_ic_sup: 2.2, significativo_fdr: false };
const modeloIpw: EfeitoApi = { ...modelo, metodo: "ipw", n_nivel: 284, n_referencia: 643, efeito_ajustado_pp: -6.1, ajustado_ic_inf: -12.7, ajustado_ic_sup: 0.4 };
const virada: EfeitoApi = { ...modeloIpw, fator: "virada_dez2023", nivel: "depois (dez/2023 em diante, GPT-4 padrão)", referencia: "antes (abr a nov/2023)" };

describe("uma linha por fator", () => {
  it("o segundo método não vira linha própria: recusa e modelo aparecem uma vez", () => {
    const { linhas } = prepararFloresta([base, ipwSem, modelo, modeloIpw], "assistente");
    expect(linhas.map((l) => l.fator).sort()).toEqual(["modelo_familia", "recusa"]);
    const r = linhas.find((l) => l.fator === "recusa")!;
    expect(r.metodo).toBe("logit_ame");
    expect(r.segundo?.ajustado).toBeNull();
    expect(linhas.find((l) => l.fator === "modelo_familia")!.segundo?.ajustado?.efeito).toBe(-6.1);
  });

  it("a frase-resposta conta só o ajuste pelo perfil; a virada (só segundo método) fica fora da contagem", () => {
    const todos = [base, ipwSem, modelo, modeloIpw, virada];
    expect(contarDistinguiveis(todos)).toEqual({ k: 1, m: 2, f: 1 });
    const { linhas } = prepararFloresta(todos, "assistente");
    expect(linhas.map((l) => l.fator)).toContain("virada_dez2023");
    expect(contarDoGrupo(linhas)).toEqual({ k: 1, m: 2 });
  });

  it("a linha mostra a frase do segundo método (com número ou 'não comparável'), sem sumir nenhum resultado", () => {
    const { linhas, limite } = prepararFloresta([base, ipwSem, modelo, modeloIpw], "assistente");
    render(<Floresta linhas={linhas} limite={limite} />);
    const m = document.querySelector('[data-fator="modelo_familia"]') as HTMLElement;
    expect(within(m).getByText(/Por outra forma de comparar pessoas parecidas \(284 contra 643\)/)).toBeTruthy();
    const r = document.querySelector('[data-fator="recusa"]') as HTMLElement;
    expect(within(r).getByText(/Por outra forma de comparar pessoas parecidas: não dá para comparar/)).toBeTruthy();
    expect(within(r).getByText("grupos não comparáveis")).toBeTruthy();
    expect(document.querySelectorAll('[data-fator="recusa"]').length).toBe(1);
  });
});

describe("títulos em frase", () => {
  it("nenhum identificador de variável vira título", () => {
    expect(tituloLinha("recusa", "sim", "não")).toBe("O assistente se recusou a responder logo na 1ª resposta, contra não se recusou");
    expect(tituloLinha("virada_dez2023", "x", "y")).not.toMatch(/virada_dez2023/);
    expect(tituloLinha("idioma", "Spanish", "Portuguese")).toBe("Idioma da pergunta: espanhol, contra português");
    expect(tituloLinha("era_modelo", "2023-07..10 (só 3.5)", "2023-12+ (4 padrão)")).toContain("jul a out/2023");
    expect(tituloLinha("fator_novo", "a", "b")).toContain("a contra b");
  });

  it("todo fator da API tem frase própria", () => {
    const titulos = (todasAsMensagens.fatores as unknown as { titulos: Record<string, string> }).titulos;
    for (const f of ["recusa", "idioma", "tema", "periodo_dia", "era_modelo", "regiao", "faixa_chars_resposta", "faixa_chars_pergunta", "fim_de_semana", "modelo_familia", "dispositivo", "idioma_divergente", "n_conversas_sessao", "n_turnos_sessao", "tema_descritivo", "virada_dez2023"]) {
      expect(titulos[f], f).toBeTruthy();
    }
  });
});

describe("cartões de achados", () => {
  it("resumir deixa 2 frases à vista e o resto no recolhível, sem quebrar em números", () => {
    const txt = "Entre 2.372 novos usuários, 132 (5,6%) receberam recusa. Voltaram 13 de 132 (9,8%), contra 553. Terceira frase. Quarta frase.";
    const r = resumir(txt);
    expect(r.visivel).toBe("Entre 2.372 novos usuários, 132 (5,6%) receberam recusa. Voltaram 13 de 132 (9,8%), contra 553.");
    expect(r.resto).toBe("Terceira frase. Quarta frase.");
    expect(resumir("Só uma frase.").resto).toBe("");
  });
});

describe("Tela 3: termos técnicos e classificadores", () => {
  const termos = (todasAsMensagens.dados as unknown as { termosTecnicos: Record<string, { inline: string; nota: string }> }).termosTecnicos;

  it("troca turn_identifier, conversation_hash, redacted e a referência à figura por texto em português", () => {
    const a = traduzirTermos("Mantidas, identificadas por turn_identifier; conversation_hash não é chave.", termos);
    expect(a.texto).toBe("Mantidas, identificadas por número do turno; o código da conversa não é chave.");
    expect(a.tecnicos.map((x) => x.termo)).toEqual(["conversation_hash", "turn_identifier"]);
    expect(traduzirTermos("Conversas com dado pessoal ocultado pelos autores (redacted)", termos).texto).toBe("Conversas com dado pessoal ocultado pelos autores");
    expect(traduzirTermos("restrito a perguntas com mais de 30 caracteres (ver figura 06).", termos).texto).not.toMatch(/figura 06/);
  });

  it("classificador por IA ou por palavras-chave vem do campo modelo", () => {
    expect(tipoClassificador("openrouter:anthropic/claude-haiku-5.5")).toBe("ia");
    expect(tipoClassificador("regras:1.1.0")).toBe("regras");
    expect(tipoClassificador(null)).toBeNull();
    expect(t("dados.validacaoLinha", { nome: "Recusa", tipo: "por IA", usado: ", usado nos números", acuracia: "92,0%", n: 200, kappa: "0,59" })).toContain("Recusa (por IA, usado nos números): acerta 92,0%");
  });
});
