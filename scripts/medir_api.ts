/**
 * Mede p50/p95 de cada endpoint (REQ-307) e grava a tabela em docs/desempenho.md.
 *
 * Roda os handlers das rotas dentro do próprio processo (sem rede HTTP) contra o banco apontado por DATABASE_URL:
 *   cd app && DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx tsx ../scripts/medir_api.ts
 *
 *   frio   = cache limpo antes de cada chamada (consulta o banco de verdade);
 *   quente = cache já preenchido (segunda chamada em diante).
 * Mede handler + banco + montagem do envelope; não inclui rede nem serialização HTTP do servidor.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { cacheRotas } from "../app/lib/api";
import { pool } from "../app/lib/db";

const CHAMADAS = 50;

type Handler = (req: Request) => Promise<Response>;
interface Alvo {
  rota: string;
  query: string;
  carregar: () => Promise<{ GET: Handler }>;
}

const alvos: Alvo[] = [
  { rota: "/api/retencao/resumo", query: "", carregar: () => import("../app/app/api/retencao/resumo/route") },
  { rota: "/api/retencao/coortes", query: "", carregar: () => import("../app/app/api/retencao/coortes/route") },
  { rota: "/api/retencao/coortes", query: "?granularidade=mes", carregar: () => import("../app/app/api/retencao/coortes/route") },
  { rota: "/api/retencao/sensibilidade", query: "", carregar: () => import("../app/app/api/retencao/sensibilidade/route") },
  { rota: "/api/dicionario", query: "", carregar: () => import("../app/app/api/dicionario/route") },
  { rota: "/api/fatores/efeitos", query: "", carregar: () => import("../app/app/api/fatores/efeitos/route") },
  { rota: "/api/fatores/segmentos", query: "?variavel=era_modelo", carregar: () => import("../app/app/api/fatores/segmentos/route") },
  { rota: "/api/fatores/balanco", query: "?tratamento=modelo_familia", carregar: () => import("../app/app/api/fatores/balanco/route") },
  { rota: "/api/semana/decomposicao", query: "?semana=2023-05-01", carregar: () => import("../app/app/api/semana/decomposicao/route") },
  { rota: "/api/achados", query: "", carregar: () => import("../app/app/api/achados/route") },
  { rota: "/api/qualidade", query: "", carregar: () => import("../app/app/api/qualidade/route") },
];

function percentil(v: number[], p: number): number {
  const o = [...v].sort((a, b) => a - b);
  const i = Math.min(o.length - 1, Math.ceil((p / 100) * o.length) - 1);
  return o[Math.max(0, i)]!;
}

async function medir(h: Handler, url: string, limpar: boolean) {
  const tempos: number[] = [];
  let status = 0;
  let hits = 0;
  for (let i = 0; i < CHAMADAS; i++) {
    if (limpar) cacheRotas.limpar();
    const t0 = performance.now();
    const r = await h(new Request(url));
    await r.text();
    tempos.push(performance.now() - t0);
    status = r.status;
  }
  void hits;
  return { p50: percentil(tempos, 50), p95: percentil(tempos, 95), status };
}

async function main() {
  if (!process.env.DATABASE_URL) throw new Error("defina DATABASE_URL (papel app_ro)");
  // Os logs de uma linha por requisição não interessam aqui.
  const log = console.log;
  const err = console.error;
  console.log = () => undefined;
  console.error = () => undefined;
  const linhas: string[] = [];
  const resultados: string[] = [];
  for (const a of alvos) {
    const { GET } = await a.carregar();
    const url = `http://x${a.rota}${a.query}`;
    await GET(new Request(url)).then((r) => r.text()); // aquecimento da conexão
    const frio = await medir(GET, url, true);
    cacheRotas.limpar();
    await GET(new Request(url)).then((r) => r.text()); // preenche o cache
    const quente = await medir(GET, url, false);
    const f = (n: number) => n.toFixed(1);
    if (frio.status !== 200 || quente.status !== 200) {
      // Erro não é desempenho: não publica tempo de uma resposta que falhou.
      linhas.push(`| \`${a.rota}${a.query}\` | n/d | n/d | n/d | n/d |`);
      resultados.push(`${a.rota}${a.query} NÃO MEDIDA (status ${frio.status}/${quente.status})`);
      continue;
    }
    linhas.push(`| \`${a.rota}${a.query}\` | ${f(frio.p50)} | ${f(frio.p95)} | ${f(quente.p50)} | ${f(quente.p95)} |`);
    resultados.push(`${a.rota}${a.query} frio p50=${f(frio.p50)} p95=${f(frio.p95)} quente p50=${f(quente.p50)} p95=${f(quente.p95)}`);
  }
  console.log = log;
  console.error = err;
  await pool().end();

  const data = new Date().toISOString().slice(0, 10);
  const md = `# Desempenho da API

Medido em ${data}. ${CHAMADAS} chamadas por rota, em milissegundos.

- **Frio**: cache em memória limpo antes de cada chamada, então cada chamada consulta o banco.
- **Quente**: resposta já no cache (mesma rota, mesmos parâmetros, mesmo lote).
- Como foi medido: os handlers das rotas rodam no próprio processo (\`scripts/medir_api.ts\`), contra um Postgres 16 local em Docker (WSL2), com o papel \`app_ro\`. **Inclui** banco, montagem do envelope e validação dos parâmetros; **não inclui** rede nem o servidor HTTP do Next.
- Toda chamada, mesmo a quente, faz uma leitura leve do último lote (para saber se o cache ainda vale).
- Máquina de desenvolvimento com pouca memória: os números servem de ordem de grandeza, não de garantia.

| Rota | frio p50 | frio p95 | quente p50 | quente p95 |
|---|---:|---:|---:|---:|
${linhas.join("\n")}

Como repetir: \`cd app && DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx tsx ../scripts/medir_api.ts\`.
Em produção as mesmas métricas saem do log JSON de uma linha por requisição (\`duracao_ms\`, \`cache\`) no CloudWatch Logs Insights, e o cabeçalho \`Server-Timing\` traz banco e total em cada resposta.
`;
  const destino = resolve(process.cwd(), "../docs/desempenho.md");
  mkdirSync(dirname(destino), { recursive: true });
  writeFileSync(destino, md, "utf8");
  for (const r of resultados) console.log(r);
  console.log("gravado em docs/desempenho.md");
}

main().catch((e) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
