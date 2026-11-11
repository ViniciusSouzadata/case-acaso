import { afterAll, describe, expect, it } from "vitest";
import { varrer } from "./helpers/varredura";
import {
  respostaAchados,
  respostaBalanco,
  respostaCoortes,
  respostaDicionario,
  respostaEfeitos,
  respostaQualidade,
  respostaResumo,
  respostaSegmentos,
  respostaSemana,
  respostaSensibilidade,
} from "@/lib/esquemas";

// Teste de fumaça: executa as rotas contra um banco REAL (papel app_ro, somente leitura) e valida com o esquema do contrato.
// Só roda com DATABASE_URL definida. Ex.: DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx vitest run tests/fumaca
const temBanco = Boolean(process.env.DATABASE_URL);

describe.skipIf(!temBanco)("fumaça contra o banco real", () => {
  afterAll(async () => {
    const { pool } = await import("@/lib/db");
    await pool().end();
  });

  const chamar = async (modulo: string, query = "") => {
    const { GET } = (await import(modulo)) as { GET: (r: Request) => Promise<Response> };
    const r = await GET(new Request(`http://x/api/t${query}`));
    return { status: r.status, corpo: (await r.json()) as unknown };
  };

  const casos = [
    ["/api/retencao/resumo", "@/app/api/retencao/resumo/route", "", respostaResumo],
    ["/api/retencao/coortes (semana)", "@/app/api/retencao/coortes/route", "", respostaCoortes],
    ["/api/retencao/coortes (mes)", "@/app/api/retencao/coortes/route", "?granularidade=mes", respostaCoortes],
    ["/api/retencao/coortes (intervalo)", "@/app/api/retencao/coortes/route", "?inicio=2023-05-01&fim=2023-08-01", respostaCoortes],
    ["/api/retencao/sensibilidade", "@/app/api/retencao/sensibilidade/route", "", respostaSensibilidade],
    ["/api/dicionario", "@/app/api/dicionario/route", "", respostaDicionario],
    ["/api/fatores/efeitos", "@/app/api/fatores/efeitos/route", "", respostaEfeitos],
    ["/api/fatores/efeitos (grupo)", "@/app/api/fatores/efeitos/route", "?grupo=perfil", respostaEfeitos],
    ["/api/fatores/segmentos", "@/app/api/fatores/segmentos/route", "?variavel=era_modelo", respostaSegmentos],
    ["/api/fatores/balanco", "@/app/api/fatores/balanco/route", "?tratamento=modelo_familia", respostaBalanco],
    ["/api/semana/decomposicao", "@/app/api/semana/decomposicao/route", "?semana=2023-05-01", respostaSemana],
    ["/api/achados", "@/app/api/achados/route", "", respostaAchados],
    ["/api/qualidade", "@/app/api/qualidade/route", "", respostaQualidade],
  ] as const;

  it.each(casos)("%s", async (_nome, modulo, query, esquema) => {
    const { status, corpo } = await chamar(modulo, query);
    const r = esquema.safeParse(corpo);
    expect(r.success, r.success ? "" : JSON.stringify(r.error.issues.slice(0, 3))).toBe(true);
    expect(status).toBe(200);
    expect(varrer(corpo), "dado sensível na resposta real").toEqual([]);
  });

  it("números oficiais batem com o STATE (2.372 elegíveis, 566 voltaram)", async () => {
    const { corpo } = await chamar("@/app/api/retencao/resumo/route");
    const d = respostaResumo.parse(corpo).dados;
    expect(d?.usuarios).toBe(2372);
    expect(d?.voltaram_7d).toBe(566);
    expect(d?.taxa).toBeCloseTo(0.2386, 3);
  });
});
