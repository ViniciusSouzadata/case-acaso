import { Pool, types, type QueryResultRow } from "pg";

// Papel app_ro: só lê mart.* e resultado.* (e ops.lote_carga, ops.reconciliacao). A URL vem do ambiente, nunca do código.
// bigint e numeric chegam do pg como texto; aqui as contagens e taxas são pequenas, então viram number.
types.setTypeParser(types.builtins.INT8, (v) => Number(v));
types.setTypeParser(types.builtins.NUMERIC, (v) => Number(v));
// date chega como "AAAA-MM-DD" (sem virar Date no fuso da máquina).
types.setTypeParser(types.builtins.DATE, (v) => v);

const global = globalThis as unknown as { __pool?: Pool };

function criarPool(): Pool {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL não definida");
  return new Pool({ connectionString: url, max: 5, statement_timeout: 10_000 });
}

export function pool(): Pool {
  global.__pool ??= criarPool();
  return global.__pool;
}

/** Consulta parametrizada. Devolve as linhas e o tempo gasto no banco (para o Server-Timing). */
export async function consultar<T extends QueryResultRow>(
  sql: string,
  params: unknown[] = [],
): Promise<{ linhas: T[]; ms: number }> {
  const t0 = performance.now();
  const r = await pool().query<T>(sql, params);
  return { linhas: r.rows, ms: performance.now() - t0 };
}
