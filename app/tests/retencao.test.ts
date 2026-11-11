import { readFileSync } from "node:fs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  esquemaErro,
  respostaCoortes,
  respostaDicionario,
  respostaResumo,
  respostaSensibilidade,
} from "@/lib/esquemas";

// Banco simulado: devolve as linhas dos exemplos conforme a tabela consultada.
const exemplo = (nome: string) => JSON.parse(readFileSync(`exemplos/${nome}.json`, "utf8")) as {
  dados: unknown;
  meta: Record<string, unknown>;
};

const chamadas: { sql: string; params: unknown[] }[] = [];

vi.mock("@/lib/db", () => ({
  consultar: vi.fn(async (sql: string, params: unknown[] = []) => {
    chamadas.push({ sql, params });
    const exCoortes = exemplo("retencao-coortes");
    if (sql.includes("FROM ops.lote_carga"))
      return { linhas: [{ lote_id: 1, versao_definicao: "1.0.0", terminado_em: "2026-11-14T12:00:00Z" }], ms: 1 };
    if (sql.includes("n_elegiveis")) return { linhas: [exemplo("retencao-resumo").dados], ms: 1 };
    if (sql.includes("SELECT versao_analise FROM resultado.meta"))
      return { linhas: [{ versao_analise: "1.0.0" }], ms: 1 };
    if (sql.includes("mart.agg_retencao_periodo")) return { linhas: exCoortes.dados, ms: 1 };
    if (sql.includes("mart.dim_era_modelo")) return { linhas: exCoortes.meta.eras, ms: 1 };
    if (sql.includes("mart.agg_retencao_sensibilidade")) return { linhas: exemplo("retencao-sensibilidade").dados, ms: 1 };
    if (sql.includes("mart.dicionario_indicador")) return { linhas: exemplo("dicionario").dados, ms: 1 };
    throw new Error("consulta inesperada: " + sql.slice(0, 40));
  }),
}));

const { GET: resumo } = await import("@/app/api/retencao/resumo/route");
const { GET: coortes } = await import("@/app/api/retencao/coortes/route");
const { GET: sensibilidade } = await import("@/app/api/retencao/sensibilidade/route");
const { GET: dicionario } = await import("@/app/api/dicionario/route");

const pedir = (rota: string, query = "") => new Request(`http://x/api/${rota}${query}`);

beforeEach(() => {
  chamadas.length = 0;
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

describe("contrato dos exemplos", () => {
  it.each([
    ["retencao-resumo", respostaResumo],
    ["retencao-coortes", respostaCoortes],
    ["retencao-sensibilidade", respostaSensibilidade],
    ["dicionario", respostaDicionario],
  ] as const)("%s bate com o esquema", (nome, esquema) => {
    expect(esquema.safeParse(exemplo(nome)).success).toBe(true);
  });

  it("falha se um campo sumir", () => {
    const e = exemplo("retencao-coortes") as { dados: Record<string, unknown>[] };
    delete e.dados[0]!["taxa_mm4"];
    expect(respostaCoortes.safeParse(e).success).toBe(false);
  });

  it("falha se um campo mudar de tipo ou aparecer um campo extra", () => {
    const a = exemplo("retencao-sensibilidade") as { dados: Record<string, unknown>[] };
    a.dados[0]!["taxa"] = "0.23";
    expect(respostaSensibilidade.safeParse(a).success).toBe(false);
    const b = exemplo("retencao-sensibilidade") as { dados: Record<string, unknown>[] };
    b.dados[0]!["hashed_ip"] = "x";
    expect(respostaSensibilidade.safeParse(b).success).toBe(false);
  });
});

describe("endpoints", () => {
  it("/retencao/resumo", async () => {
    const r = await resumo(pedir("retencao/resumo"));
    expect(r.status).toBe(200);
    expect(r.headers.get("Server-Timing")).toMatch(/^db;dur=/);
    expect(respostaResumo.safeParse(await r.json()).success).toBe(true);
  });

  it("/retencao/coortes traz meta.eras e passa as datas como parâmetro (SQL parametrizado)", async () => {
    const r = await coortes(pedir("retencao/coortes", "?granularidade=mes&inicio=2023-05-01&fim=2023-08-01"));
    expect(r.status).toBe(200);
    const corpo = respostaCoortes.parse(await r.json());
    expect(corpo.meta.eras.length).toBeGreaterThan(0);
    const c = chamadas.find((x) => x.sql.includes("mart.agg_retencao_periodo"))!;
    expect(c.params).toEqual(["mes", "2023-05-01", "2023-08-01"]);
    expect(c.sql).not.toContain("2023-05-01");
  });

  it("/retencao/coortes usa semana e período todo por padrão", async () => {
    await coortes(pedir("retencao/coortes"));
    const c = chamadas.find((x) => x.sql.includes("mart.agg_retencao_periodo"))!;
    expect(c.params).toEqual(["semana", null, null]);
  });

  it("/retencao/sensibilidade e /dicionario", async () => {
    expect(respostaSensibilidade.safeParse(await (await sensibilidade(pedir("retencao/sensibilidade"))).json()).success).toBe(true);
    expect(respostaDicionario.safeParse(await (await dicionario(pedir("dicionario", "?indicador=taxa_retorno_7d"))).json()).success).toBe(true);
    expect(chamadas.find((x) => x.sql.includes("dicionario_indicador"))!.params).toEqual(["taxa_retorno_7d"]);
  });
});

describe("erros 400", () => {
  const casos: [string, () => Promise<Response>, RegExp][] = [
    ["país não carregado", () => resumo(pedir("retencao/resumo", "?pais=Argentina")), /país ainda não carregado/],
    ["país em coortes", () => coortes(pedir("retencao/coortes", "?pais=Chile")), /país ainda não carregado/],
    ["país em sensibilidade", () => sensibilidade(pedir("retencao/sensibilidade", "?pais=Chile")), /país ainda não carregado/],
    ["data mal formada", () => coortes(pedir("retencao/coortes", "?inicio=ontem")), /AAAA-MM-DD/],
    ["data inexistente", () => coortes(pedir("retencao/coortes", "?fim=2023-02-30")), /data inexistente/],
    ["intervalo invertido", () => coortes(pedir("retencao/coortes", "?inicio=2023-09-01&fim=2023-05-01")), /invertido/],
    ["granularidade", () => coortes(pedir("retencao/coortes", "?granularidade=dia")), /granularidade/],
  ];

  it.each(casos)("%s", async (_nome, chamar, mensagem) => {
    const r = await chamar();
    expect(r.status).toBe(400);
    const corpo = esquemaErro.parse(await r.json());
    expect(corpo.erro.codigo).toBe("PARAMETRO_INVALIDO");
    expect(corpo.erro.mensagem).toMatch(mensagem);
  });

  it("erro 400 não consulta as tabelas de dados", async () => {
    await coortes(pedir("retencao/coortes", "?inicio=2023-09-01&fim=2023-05-01"));
    expect(chamadas.some((x) => x.sql.includes("mart.agg_retencao_periodo"))).toBe(false);
  });
});
