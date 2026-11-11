import { describe, expect, it } from "vitest";
import {
  formatarLog,
  formatarServerTiming,
  montarEnvelope,
  montarErro,
  novoRequestId,
  type LinhaLog,
} from "@/lib/api";

const meta = {
  versao_definicao: "1.0.0",
  versao_analise: "1.0.0",
  atualizado_em: "2026-11-14T12:00:00.000Z",
  lote_id: 3,
  request_id: "req_ab12cd",
  fonte: "mart.agg_retencao_periodo",
};

describe("envelope", () => {
  it("traz dados e a meta obrigatória (REQ-304)", () => {
    const e = montarEnvelope([{ a: 1 }], meta);
    expect(Object.keys(e).sort()).toEqual(["dados", "meta"]);
    for (const campo of ["versao_definicao", "versao_analise", "atualizado_em", "lote_id", "request_id", "fonte"]) {
      expect(e.meta).toHaveProperty(campo);
    }
    expect(e.dados).toEqual([{ a: 1 }]);
  });

  it("erro segue o formato padronizado", () => {
    expect(montarErro("PARAMETRO_INVALIDO", "pais inválido", "req_1")).toEqual({
      erro: { codigo: "PARAMETRO_INVALIDO", mensagem: "pais inválido", request_id: "req_1" },
    });
  });

  it("request_id tem prefixo e é diferente a cada chamada", () => {
    const a = novoRequestId();
    const b = novoRequestId();
    expect(a).toMatch(/^req_[0-9a-f]{6}$/);
    expect(a).not.toBe(b);
  });
});

describe("log", () => {
  const linha: LinhaLog = {
    request_id: "req_ab12cd",
    endpoint: "/api/saude",
    params: { pais: "Brazil" },
    status: 200,
    duracao_ms: 12.3456,
    linhas: 1,
    lote_id: 3,
    cache: "miss",
  };

  it("é uma linha JSON com os campos do REQ-305", () => {
    const texto = formatarLog(linha);
    expect(texto).not.toContain("\n");
    const o = JSON.parse(texto) as Record<string, unknown>;
    expect(Object.keys(o).sort()).toEqual(
      ["cache", "duracao_ms", "endpoint", "linhas", "lote_id", "params", "request_id", "status"].sort(),
    );
    expect(o.duracao_ms).toBe(12.3);
    expect(o.cache).toBe("miss");
  });

  it("Server-Timing traz tempo de banco e total", () => {
    expect(formatarServerTiming(3.14159, 12.5)).toBe("db;dur=3.1, total;dur=12.5");
  });
});
