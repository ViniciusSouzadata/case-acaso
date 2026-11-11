import { beforeEach, describe, expect, it, vi } from "vitest";
import { CacheTTL, TTL_PADRAO_MS } from "@/lib/cache";

describe("CacheTTL", () => {
  let agora = 1_000;
  let c: CacheTTL<string>;
  beforeEach(() => {
    agora = 1_000;
    c = new CacheTTL<string>(TTL_PADRAO_MS, () => agora);
  });

  it("guarda e devolve (hit); ausente é undefined (miss)", () => {
    const k = CacheTTL.chave("/api/x", { a: "1" }, 3);
    expect(c.obter(k)).toBeUndefined();
    c.guardar(k, "v");
    expect(c.obter(k)).toBe("v");
  });

  it("expira depois de 1 h", () => {
    const k = CacheTTL.chave("/api/x", {}, 3);
    c.guardar(k, "v");
    agora += TTL_PADRAO_MS - 1;
    expect(c.obter(k)).toBe("v");
    agora += 1;
    expect(c.obter(k)).toBeUndefined();
    expect(c.tamanho).toBe(0);
  });

  it("lote novo invalida: a chave muda com o lote_id", () => {
    const k3 = CacheTTL.chave("/api/x", { a: "1" }, 3);
    const k4 = CacheTTL.chave("/api/x", { a: "1" }, 4);
    expect(k3).not.toBe(k4);
    c.guardar(k3, "velho");
    expect(c.obter(k4)).toBeUndefined();
  });

  it("a ordem dos parâmetros não muda a chave; parâmetros diferentes mudam", () => {
    expect(CacheTTL.chave("/a", { x: "1", y: "2" }, 1)).toBe(CacheTTL.chave("/a", { y: "2", x: "1" }, 1));
    expect(CacheTTL.chave("/a", { x: "1" }, 1)).not.toBe(CacheTTL.chave("/a", { x: "2" }, 1));
    expect(CacheTTL.chave("/a", {}, 1)).not.toBe(CacheTTL.chave("/b", {}, 1));
  });

  it("não passa do limite de entradas", () => {
    const p = new CacheTTL<number>(TTL_PADRAO_MS, () => agora, 3);
    for (let i = 0; i < 10; i++) p.guardar("k" + i, i);
    expect(p.tamanho).toBeLessThanOrEqual(3);
  });
});

// Integração com a rota: segunda chamada igual é hit; lote novo é miss; erro e saúde não vão para o cache.
const estado = { lote: 1, consultasDeDados: 0 };
vi.mock("@/lib/db", () => ({
  consultar: vi.fn(async (sql: string) => {
    if (sql.includes("FROM ops.lote_carga"))
      return { linhas: [{ lote_id: estado.lote, versao_definicao: "1.0.0", terminado_em: "2026-11-14T12:00:00Z" }], ms: 1 };
    if (sql.includes("SELECT versao_analise FROM resultado.meta")) return { linhas: [{ versao_analise: "1.0.0" }], ms: 1 };
    estado.consultasDeDados += 1;
    return { linhas: [], ms: 1 };
  }),
}));

describe("cache na rota", () => {
  const logs: string[] = [];
  beforeEach(async () => {
    const { cacheRotas } = await import("@/lib/api");
    cacheRotas.limpar();
    estado.lote = 1;
    estado.consultasDeDados = 0;
    logs.length = 0;
    vi.spyOn(console, "log").mockImplementation((l: string) => void logs.push(l));
  });

  const pedir = (q = "") => new Request(`http://x/api/achados${q}`);
  const cacheDoUltimoLog = () => (JSON.parse(logs[logs.length - 1]!) as { cache: string }).cache;

  it("2ª chamada igual é hit e não volta ao banco; o request_id é novo", async () => {
    const { GET } = await import("@/app/api/achados/route");
    const a = await GET(pedir());
    expect(cacheDoUltimoLog()).toBe("miss");
    const b = await GET(pedir());
    expect(cacheDoUltimoLog()).toBe("hit");
    expect(estado.consultasDeDados).toBe(1);
    const [ja, jb] = [await a.json(), await b.json()];
    expect(jb.dados).toEqual(ja.dados);
    expect(jb.meta.request_id).not.toBe(ja.meta.request_id);
    expect(b.headers.get("Cache-Control")).toBe("public, s-maxage=300, stale-while-revalidate=3600");
  });

  it("lote novo invalida", async () => {
    const { GET } = await import("@/app/api/achados/route");
    await GET(pedir());
    estado.lote = 2;
    await GET(pedir());
    expect(cacheDoUltimoLog()).toBe("miss");
    expect(estado.consultasDeDados).toBe(2);
  });

  it("erro 400 não é cacheado e vem com no-store", async () => {
    const { GET } = await import("@/app/api/achados/route");
    const r = await GET(pedir("?pais=Chile"));
    expect(r.status).toBe(400);
    expect(r.headers.get("Cache-Control")).toBe("no-store");
    await GET(pedir("?pais=Chile"));
    expect(cacheDoUltimoLog()).toBe("miss");
  });

  it("/api/saude nunca usa cache", async () => {
    const { GET } = await import("@/app/api/saude/route");
    const r = await GET(new Request("http://x/api/saude"));
    await GET(new Request("http://x/api/saude"));
    expect(cacheDoUltimoLog()).toBe("miss");
    expect(r.headers.get("Cache-Control")).toBe("no-store");
  });
});
