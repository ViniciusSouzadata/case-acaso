import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { cacheRotas } from "@/lib/api";
import { varrer } from "./helpers/varredura";

vi.mock("@/lib/db", async () => {
  const { consultarSimulado } = await import("./helpers/banco-simulado");
  return { consultar: vi.fn(consultarSimulado) };
});

const RAIZ_API = "app/api";

function listar(dir: string, filtro: (f: string) => boolean): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? listar(p, filtro) : filtro(p) ? [p] : [];
  });
}

/** "app/api/fatores/efeitos/route.ts" → "/api/fatores/efeitos" */
const rotaDe = (arq: string) => "/" + relative("app", arq).split(sep).slice(0, -1).join("/");

// Parâmetros mínimos para cada rota responder 200.
const QUERY: Record<string, string> = {
  "/api/fatores/segmentos": "?variavel=era_modelo",
  "/api/fatores/balanco": "?tratamento=modelo_familia",
  "/api/semana/decomposicao": "?semana=2023-05-01",
};

const rotasNoDisco = listar(RAIZ_API, (f) => f.endsWith("route.ts")).sort();

describe("o detector de varredura não é cego", () => {
  it.each([
    [{ hashed_ip: "x" }, "chave proibida"],
    [{ a: { user_agent: "x" } }, "chave proibida"],
    [{ a: ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"] }, "hash"],
    [{ a: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" }, "user-agent"],
    [{ a: "acessou de 200.158.10.4 ontem" }, "IPv4"],
    [{ pergunta: "como faço um bolo?" }, "chave proibida"],
  ])("pega %j", (obj, parte) => {
    const a = varrer(obj);
    expect(a.length).toBeGreaterThan(0);
    expect(a.map((x) => x.motivo).join(" ")).toContain(parte);
  });

  it("não acusa dado agregado normal", () => {
    expect(varrer({ taxa: 0.2386, versao_definicao: "1.0.0", periodo: "2023-05-01", nota: "user-agents distintos por IP" })).toEqual([]);
  });
});

describe("nenhuma resposta de nenhuma rota tem hashed_ip, user-agent nem texto de conversa", () => {
  beforeEach(() => {
    cacheRotas.limpar();
    vi.spyOn(console, "log").mockImplementation(() => undefined);
  });

  it("todas as rotas do disco são varridas (rota nova sem cobertura faz o teste falhar)", () => {
    const esperadas = [
      "/api/achados", "/api/dicionario", "/api/fatores/balanco", "/api/fatores/efeitos", "/api/fatores/segmentos",
      "/api/qualidade", "/api/retencao/coortes", "/api/retencao/resumo", "/api/retencao/sensibilidade",
      "/api/saude", "/api/semana/decomposicao",
    ];
    expect(rotasNoDisco.map(rotaDe).sort()).toEqual(esperadas);
  });

  it.each(rotasNoDisco)("%s", async (arq) => {
    const rota = rotaDe(arq);
    const { GET } = (await import(`@/${arq.replace(/\.ts$/, "")}`)) as { GET: (r: Request) => Promise<Response> };
    const r = await GET(new Request(`http://x${rota}${QUERY[rota] ?? ""}`));
    expect(r.status).toBe(200);
    const corpo = await r.json();
    expect(varrer(corpo)).toEqual([]);
  });
});

describe("a aplicação só lê o que pode ler (REQ-301)", () => {
  const fontes = [...listar("lib/consultas", (f) => f.endsWith(".ts")), "lib/meta.ts"];
  const PERMITIDAS = new Set([
    "mart.agg_retencao_periodo", "mart.agg_retencao_sensibilidade", "mart.agg_retencao_segmento",
    "mart.dicionario_indicador", "mart.dim_era_modelo",
    "resultado.meta", "resultado.efeito_fator", "resultado.balanco_propensao", "resultado.decomposicao_semana",
    "resultado.decomposicao_resumo", "resultado.sensibilidade_efeito", "resultado.validacao_classificador",
    "resultado.achado", "resultado.problema_qualidade",
    "ops.lote_carga", "ops.reconciliacao",
  ]);

  it("existem consultas para examinar", () => {
    expect(fontes.length).toBeGreaterThanOrEqual(5);
  });

  it.each(fontes)("%s não referencia stg.", (arq) => {
    expect(readFileSync(arq, "utf8")).not.toMatch(/\bstg\./i);
  });

  it.each(fontes)("%s só consulta tabelas permitidas", (arq) => {
    const usadas = [...readFileSync(arq, "utf8").matchAll(/\b(?:FROM|JOIN)\s+((?:mart|resultado|ops|stg|public)\.\w+)/gi)].map((m) => m[1]!.toLowerCase());
    for (const t of usadas) expect(PERMITIDAS.has(t), `${arq} consulta ${t}`).toBe(true);
  });

  it("nenhuma tabela de fatos por usuário (mart.fct_*) nem dim_usuario é lida", () => {
    for (const arq of fontes) expect(readFileSync(arq, "utf8")).not.toMatch(/mart\.(fct_|dim_usuario)/i);
  });

  it("nenhum SQL é montado por concatenação de texto", () => {
    for (const arq of fontes) expect(readFileSync(arq, "utf8"), arq).not.toMatch(/\$\{[^}]*\}[^`]*(FROM|WHERE)|(FROM|WHERE)[^`]*\$\{/is);
  });
});
