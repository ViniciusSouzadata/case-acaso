import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { cacheRotas } from "@/lib/api";
import {
  esquemaErro,
  respostaAchados,
  respostaBalanco,
  respostaEfeitos,
  respostaQualidade,
  respostaSegmentos,
  respostaSemana,
} from "@/lib/esquemas";

type Ex = { dados: any; meta: Record<string, unknown> };
const exemplo = (nome: string) => JSON.parse(readFileSync(`exemplos/${nome}.json`, "utf8")) as Ex;

const estado = { vazio: false };
const chamadas: { sql: string; params: unknown[] }[] = [];

vi.mock("@/lib/db", () => ({
  consultar: vi.fn(async (sql: string, params: unknown[] = []) => {
    chamadas.push({ sql, params });
    const dados = (nome: string) => (estado.vazio ? [] : (exemplo(nome).dados as unknown[]));
    if (sql.includes("FROM ops.lote_carga WHERE status") && sql.includes("iniciado_em"))
      return { linhas: estado.vazio ? [] : [exemplo("qualidade").dados.lote], ms: 1 };
    if (sql.includes("FROM ops.lote_carga"))
      return { linhas: [{ lote_id: 1, versao_definicao: "1.0.0", terminado_em: "2026-11-14T12:00:00Z" }], ms: 1 };
    if (sql.includes("SELECT versao_analise FROM resultado.meta")) return { linhas: [{ versao_analise: "1.0.0" }], ms: 1 };
    if (sql.includes("resultado.efeito_fator")) return { linhas: dados("fatores-efeitos"), ms: 1 };
    if (sql.includes("mart.agg_retencao_segmento")) return { linhas: dados("fatores-segmentos"), ms: 1 };
    if (sql.includes("resultado.balanco_propensao")) return { linhas: dados("fatores-balanco"), ms: 1 };
    if (sql.includes("resultado.decomposicao_resumo"))
      return { linhas: estado.vazio ? [] : [exemplo("semana-decomposicao").dados.resumo], ms: 1 };
    if (sql.includes("resultado.decomposicao_semana"))
      return { linhas: estado.vazio ? [] : exemplo("semana-decomposicao").dados.segmentos, ms: 1 };
    if (sql.includes("resultado.achado")) return { linhas: dados("achados"), ms: 1 };
    if (sql.includes("ops.reconciliacao")) return { linhas: estado.vazio ? [] : exemplo("qualidade").dados.reconciliacao, ms: 1 };
    if (sql.includes("resultado.problema_qualidade")) return { linhas: estado.vazio ? [] : exemplo("qualidade").dados.problemas, ms: 1 };
    if (sql.includes("resultado.validacao_classificador")) return { linhas: estado.vazio ? [] : exemplo("qualidade").dados.validacao, ms: 1 };
    throw new Error("consulta inesperada: " + sql.slice(0, 50));
  }),
}));

const { GET: efeitos } = await import("@/app/api/fatores/efeitos/route");
const { GET: segmentos } = await import("@/app/api/fatores/segmentos/route");
const { GET: balanco } = await import("@/app/api/fatores/balanco/route");
const { GET: semana } = await import("@/app/api/semana/decomposicao/route");
const { GET: achados } = await import("@/app/api/achados/route");
const { GET: qualidade } = await import("@/app/api/qualidade/route");

const pedir = (rota: string, query = "") => new Request(`http://x/api/${rota}${query}`);

beforeEach(() => {
  cacheRotas.limpar();
  estado.vazio = false;
  chamadas.length = 0;
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

const rotas = [
  ["fatores/efeitos", "", efeitos, respostaEfeitos],
  ["fatores/segmentos", "?variavel=era_modelo", segmentos, respostaSegmentos],
  ["fatores/balanco", "?tratamento=gpt4", balanco, respostaBalanco],
  ["semana/decomposicao", "?semana=2023-05-01", semana, respostaSemana],
  ["achados", "", achados, respostaAchados],
  ["qualidade", "", qualidade, respostaQualidade],
] as const;

describe("contrato dos exemplos", () => {
  it.each([
    ["fatores-efeitos", respostaEfeitos],
    ["fatores-segmentos", respostaSegmentos],
    ["fatores-balanco", respostaBalanco],
    ["semana-decomposicao", respostaSemana],
    ["achados", respostaAchados],
    ["qualidade", respostaQualidade],
  ] as const)("%s bate com o esquema", (nome, esquema) => {
    expect(esquema.safeParse(exemplo(nome)).success).toBe(true);
  });

  it("falha se um campo sumir ou mudar de tipo", () => {
    const e = exemplo("fatores-efeitos");
    delete e.dados[0].e_value;
    expect(respostaEfeitos.safeParse(e).success).toBe(false);
    const q = exemplo("qualidade");
    q.dados.reconciliacao[0].ok = "sim";
    expect(respostaQualidade.safeParse(q).success).toBe(false);
  });
});

describe("endpoints", () => {
  it.each(rotas)("%s responde 200 no formato do contrato", async (rota, query, handler, esquema) => {
    const r = await handler(pedir(rota, query));
    expect(r.status).toBe(200);
    expect(esquema.safeParse(await r.json()).success).toBe(true);
  });

  it("filtros viram parâmetros, não texto de SQL", async () => {
    await efeitos(pedir("fatores/efeitos", "?grupo=perfil"));
    await segmentos(pedir("fatores/segmentos", "?variavel=era_modelo"));
    await balanco(pedir("fatores/balanco", "?tratamento=gpt4"));
    await semana(pedir("semana/decomposicao", "?semana=2023-05-01"));
    const por = (t: string) => chamadas.find((c) => c.sql.includes(t))!;
    expect(por("resultado.efeito_fator").params).toEqual(["perfil"]);
    expect(por("mart.agg_retencao_segmento").params).toEqual(["era_modelo"]);
    expect(por("resultado.balanco_propensao").params).toEqual(["gpt4"]);
    expect(por("resultado.decomposicao_resumo").params).toEqual(["2023-05-01"]);
    for (const c of chamadas) expect(c.sql).not.toMatch(/era_modelo'|gpt4|perfil'/);
  });
});

describe("tabela vazia devolve dados vazios com 200", () => {
  beforeEach(() => {
    estado.vazio = true;
  });

  it.each(["fatores/efeitos", "achados"] as const)("%s", async (rota) => {
    const h = rota === "achados" ? achados : efeitos;
    const r = await h(pedir(rota));
    expect(r.status).toBe(200);
    expect((await r.json()).dados).toEqual([]);
  });

  it("segmentos e balanço", async () => {
    expect((await (await segmentos(pedir("fatores/segmentos", "?variavel=x"))).json()).dados).toEqual([]);
    expect((await (await balanco(pedir("fatores/balanco", "?tratamento=x"))).json()).dados).toEqual([]);
  });

  it("semana sem linhas: resumo nulo e segmentos vazios", async () => {
    const r = await semana(pedir("semana/decomposicao", "?semana=2023-05-01"));
    expect(r.status).toBe(200);
    const corpo = respostaSemana.parse(await r.json());
    expect(corpo.dados).toEqual({ resumo: null, segmentos: [] });
  });

  it("qualidade sem nada: lote nulo e listas vazias", async () => {
    const r = await qualidade(pedir("qualidade"));
    expect(r.status).toBe(200);
    expect(respostaQualidade.parse(await r.json()).dados).toEqual({
      lote: null,
      reconciliacao: [],
      problemas: [],
      validacao: [],
    });
  });
});

describe("erros 400", () => {
  const casos: [string, () => Promise<Response>, RegExp][] = [
    ["país", () => efeitos(pedir("fatores/efeitos", "?pais=Chile")), /país ainda não carregado/],
    ["grupo inválido", () => efeitos(pedir("fatores/efeitos", "?grupo=outro")), /grupo/],
    ["variavel obrigatória", () => segmentos(pedir("fatores/segmentos")), /variavel/],
    ["tratamento obrigatório", () => balanco(pedir("fatores/balanco")), /tratamento/],
    ["semana obrigatória", () => semana(pedir("semana/decomposicao")), /semana/],
    ["semana inválida", () => semana(pedir("semana/decomposicao", "?semana=31-12-2023")), /AAAA-MM-DD/],
    ["país em achados", () => achados(pedir("achados", "?pais=Chile")), /país ainda não carregado/],
    ["país em qualidade", () => qualidade(pedir("qualidade", "?pais=Chile")), /país ainda não carregado/],
  ];

  it.each(casos)("%s", async (_n, chamar, msg) => {
    const r = await chamar();
    expect(r.status).toBe(400);
    const c = esquemaErro.parse(await r.json());
    expect(c.erro.codigo).toBe("PARAMETRO_INVALIDO");
    expect(c.erro.mensagem).toMatch(msg);
  });
});
