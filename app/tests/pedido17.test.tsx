// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DetalheTaxa } from "@/components/DetalheTaxa";
import { ordenarDicionario } from "@/components/DetalheQualidade";
import { Ranking } from "@/components/Ranking";
import { marcasMes, tetoEixo } from "@/components/graficos/GraficoTaxa";
import { pontosSensibilidade, prepararCoortes, type CoorteApi, type ResumoSemanaApi } from "@/lib/graficos";
import { prepararFloresta, type EfeitoApi } from "@/lib/floresta";
import { conclusaoSemana, quadroProblema, tituloProblema } from "@/lib/painel";

const mock = vi.hoisted(() => ({ coortes: [] as unknown[] }));
vi.mock("@/lib/useApi", () => ({ useApi: () => ({ estado: "ok", corpo: { dados: mock.coortes, meta: { eras: [] } } }) }));

afterEach(cleanup);

const coorte = (i: number, madura = true, gran: "mes" | "semana" = "mes"): CoorteApi => ({
  periodo: gran === "mes" ? `2023-${String(i + 1).padStart(2, "0")}-01` : `2023-01-${String(i + 1).padStart(2, "0")}`,
  novos: 200,
  voltaram_7d: madura ? 50 : null,
  taxa: madura ? 0.25 : null,
  ic_inf: 0.2,
  ic_sup: 0.3,
  taxa_mm4: null,
  amostra_suficiente: true,
  madura,
  inicio_coleta: false,
});

const resumo = (delta: number, taxa: number, mix: number, p: number | null): ResumoSemanaApi =>
  ({ semana: "2023-11-20", base_descricao: null, n_base: 197, n_semana: 65, taxa_base: 0.26, taxa_semana: 0.21, delta_pp: delta, mix_pp: mix, taxa_pp: taxa, p_valor: p, conclusao: null }) as unknown as ResumoSemanaApi;

describe("pedido 17 — cartão das semanas conforme o dado", () => {
  it("dentro da oscilação normal: não afirma queda", () => {
    const c = conclusaoSemana(resumo(-5, -4.4, -0.5, 0.13))!;
    expect(c.normal).toBe(true);
    expect(c.frase).toBe("Não dá para dizer que caiu: a diferença cabe na oscilação normal. O público não mudou.");
    expect(conclusaoSemana(resumo(5, 4.4, 0.5, 0.43))!.frase).toContain("Não dá para dizer que subiu");
  });
  it("fora do normal: mantém a frase afirmativa", () => {
    const c = conclusaoSemana(resumo(-17, -17.8, 0.7, 0.01))!;
    expect(c.normal).toBe(false);
    expect(c.frase).toBe("As pessoas voltaram menos; o público não mudou.");
  });
});

describe("pedido 17 — concordância e legenda do detalhe do gráfico", () => {
  it("mês: '1 dos 13 meses ainda está dentro dos 7 dias' (singular) e só itens que existem", () => {
    mock.coortes = [...Array.from({ length: 12 }, (_, i) => coorte(i)), coorte(12, false)];
    render(<DetalheTaxa />);
    expect(document.body.textContent).toContain("1 dos 13 meses ainda está dentro dos 7 dias. Não é uma queda.");
    const leg = screen.getAllByRole("list", { name: "Como ler o gráfico" })[0]!.textContent!;
    expect(leg).not.toContain("média das últimas 4 semanas");
    expect(leg).toContain("taxa de cada mês");
    expect(leg).toContain("ainda dentro dos 7 dias");
  });
  it("semana: plural e 'das semanas'", () => {
    mock.coortes = [...Array.from({ length: 5 }, (_, i) => coorte(i, true, "semana")), coorte(5, false, "semana"), coorte(6, false, "semana")];
    render(<DetalheTaxa />);
    fireEvent.click(screen.getByRole("button", { name: "Ver por semana" }));
    expect(document.body.textContent).toContain("2 das 7 semanas ainda estão dentro dos 7 dias. Não são uma queda.");
  });
});

describe("pedido 18 — retoques de texto", () => {
  it("legenda do ponto vazado fala de mês na visão por mês, sem 'também'", () => {
    const l = { ...coorte(0), inicio_coleta: true };
    mock.coortes = [l, ...Array.from({ length: 4 }, (_, i) => coorte(i + 1))];
    render(<DetalheTaxa />);
    const leg = screen.getAllByRole("list", { name: "Como ler o gráfico" })[0]!.textContent!;
    expect(leg).toContain("Ponto vazado: pouca gente no mês ou início da coleta");
    expect(leg).not.toContain("também");
    expect(leg).not.toContain("semanas do início");
  });
  it("dado pessoal escondido tem moldura própria", () => {
    const q = quadroProblema({ problema: "Conversas com dado pessoal ocultado pelos autores (redacted)", contagem: 56, percentual: 0.0048 }, (n) => String(n), (x) => `${((x ?? 0) * 100).toFixed(1).replace(".", ",")}%`)!;
    expect(q.frase).toBe("Em 56 conversas (0,5%) os autores da base esconderam dados pessoais.");
    expect(q.fez).toBe("mantivemos; o texto já veio sem os dados pessoais.");
  });
});

describe("pedido 17 — eixo do gráfico", () => {
  it("mês: marca a cada 2 meses, sem pular fev/24, com a última marca no último mês", () => {
    const meses = ["2023-04-01", "2023-05-01", "2023-06-01", "2023-07-01", "2023-08-01", "2023-09-01", "2023-10-01", "2023-11-01", "2023-12-01", "2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"];
    const linhas = prepararCoortes(meses.map((periodo) => ({ ...coorte(0), periodo })), "mes");
    const m = marcasMes(linhas);
    expect(m).toContain("2024-02-01");
    expect(m[m.length - 1]).toBe("2024-04-01");
    expect(m.length).toBe(7);
  });
  it("o teto do eixo cabe a faixa de margem de erro inteira", () => {
    const linhas = prepararCoortes([{ ...coorte(0), ic_inf: 0.1, ic_sup: 0.787 }], "semana");
    expect(tetoEixo(linhas)).toBe(80);
  });
});

describe("pedido 17 — formas de contar: oficial primeiro, depois da menor para a maior taxa", () => {
  it("ordena", () => {
    const f = (definicao: string, taxa: number) => ({ definicao, taxa, ic_inf: taxa - 0.02, ic_sup: taxa + 0.02, delta_vs_oficial: 0 }) as never;
    const { pontos } = pontosSensibilidade([f("a", 0.3), f("oficial", 0.24), f("b", 0.17), f("c", 0.25)]);
    expect(pontos.map((p) => p.definicao)).toEqual(["oficial", "b", "c", "a"]);
  });
});

describe("pedido 17 — Tela 2", () => {
  const ef = (fator: string, nivel: string, grupo: EfeitoApi["grupo"], aj: number | null, br: number): EfeitoApi => ({
    fator,
    nivel,
    referencia: "y",
    grupo,
    n_nivel: 300,
    n_referencia: 2000,
    taxa_nivel: 0.2,
    taxa_referencia: 0.25,
    efeito_bruto_pp: br,
    bruto_ic_inf: br - 4,
    bruto_ic_sup: br + 4,
    efeito_ajustado_pp: aj,
    ajustado_ic_inf: aj === null ? null : aj - 4,
    ajustado_ic_sup: aj === null ? null : aj + 4,
    p_valor: 0.01,
    significativo_fdr: false,
    e_value: 1.2,
    metodo: "logit_ame",
    amostra_suficiente: true,
    leitura: null,
    ordem: null,
  });
  const dados = [
    ef("idioma", "Spanish", "perfil", 15, 18),
    ef("tema", "conversa pessoal/conselho", "perfil", -8.2, -10),
    ef("tema_descritivo", "conversa pessoal/conselho", "perfil", null, -9.2),
    ef("n_conversas_sessao", "2", "engajamento", null, 8),
  ];

  it("a aba do perfil não traz linhas de assunto; o assunto fica só na aba Assunto, com o valor entre pessoas parecidas guardado para o técnico", () => {
    expect(prepararFloresta(dados, "perfil").linhas.map((l) => l.fator)).toEqual(["idioma"]);
    const ass = prepararFloresta(dados, "descritivo").linhas;
    expect(ass.length).toBe(1);
    expect(ass[0]!.entreParecidas?.efeito).toBe(-8.2);
  });

  it("a aba se chama 'A pessoa e a pergunta' e a fonte muda por aba", () => {
    render(<Ranking efeitos={dados} base={2372} />);
    expect(screen.getByRole("tab", { name: "A pessoa e a pergunta" })).toBeTruthy();
    expect(screen.getByTestId("fonte-ranking").textContent).toBe("Base: 2.372 pessoas novas · comparação entre pessoas parecidas · WildChat-1M, Brasil");
    fireEvent.click(screen.getByRole("tab", { name: "Quanto usou" }));
    expect(screen.getByTestId("fonte-ranking").textContent).toBe("Base: 2.372 pessoas novas · comparação direta, sem igualar os grupos · WildChat-1M, Brasil");
    fireEvent.click(screen.getByRole("tab", { name: "Assunto" }));
    expect(screen.getByTestId("fonte-ranking").textContent).toContain("comparação direta, sem igualar os grupos");
  });
});

describe("pedido 17 — Tela 3", () => {
  const fmt = (n: number | null) => String(n);
  const pct = (x: number | null) => `${((x ?? 0) * 100).toFixed(1).replace(".", ",")}%`;
  it("molduras em linguagem comum, com os números do dado", () => {
    const q = quadroProblema({ problema: "Idioma divergente em pergunta curta (≤ 30 caracteres): provável erro de detecção", contagem: 964, percentual: 0.083 }, fmt, pct)!;
    expect(q.frase).toBe("Em perguntas muito curtas (até 30 letras), o idioma detectado costuma estar errado. 964 conversas (8,3%).");
    expect(q.fez).toContain("mais de 30 letras");
    expect(quadroProblema({ problema: "Semanas com queda forte de volume", contagem: 4, percentual: 0.07 }, fmt, pct)!.frase).toBe("Em 4 semanas (7,0%) o número de conversas caiu muito.");
    expect(quadroProblema({ problema: "Conversa sem nenhuma mensagem do usuário (não conta como uso)", contagem: 76, percentual: 0.0065 }, fmt, pct)!.frase).toBe("76 conversas (0,7%) não têm nenhuma mensagem da pessoa.");
    expect(tituloProblema("Conversa sem nenhuma mensagem do usuário (x)")).toBe("Conversa sem mensagem da pessoa");
  });
});

describe("pedido 17 — dicionário", () => {
  it("7 principais primeiro, depois os demais em ordem alfabética", () => {
    const nomes: Record<string, string> = { zebra: "Zebra", alfa: "Alfa", beta: "Beta" };
    const itens = ["zebra", "trafego_anomalo", "alfa", "usuario", "ic_95", "sessao", "amostra_suficiente", "novos_usuarios", "taxa_retorno_7d", "beta"].map((k) => ({ indicador: k, nome_exibicao: nomes[k] ?? k }));
    const { principais, outros } = ordenarDicionario(itens);
    expect(principais.map((i) => i.indicador)).toEqual(["usuario", "novos_usuarios", "sessao", "taxa_retorno_7d", "ic_95", "amostra_suficiente", "trafego_anomalo"]);
    expect(outros.map((i) => i.nome_exibicao)).toEqual(["Alfa", "Beta", "Zebra"]);
  });
});
