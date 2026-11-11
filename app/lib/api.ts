import { NextResponse } from "next/server";
import { randomBytes } from "node:crypto";
import { lerMeta, type MetaBase } from "./meta";

export type Meta = MetaBase & { request_id: string; fonte: string } & Record<string, unknown>;

export interface Envelope<T> {
  dados: T;
  meta: Meta;
}

export interface ErroApi {
  erro: { codigo: string; mensagem: string; request_id: string };
}

/** Erro previsto: vira JSON padronizado com o status HTTP indicado. */
export class ErroHttp extends Error {
  constructor(
    public status: number,
    public codigo: string,
    mensagem: string,
  ) {
    super(mensagem);
  }
}

export function novoRequestId(): string {
  return "req_" + randomBytes(3).toString("hex");
}

export function montarEnvelope<T>(dados: T, meta: Meta): Envelope<T> {
  return { dados, meta };
}

export function montarErro(codigo: string, mensagem: string, request_id: string): ErroApi {
  return { erro: { codigo, mensagem, request_id } };
}

export interface LinhaLog {
  request_id: string;
  endpoint: string;
  params: Record<string, string>;
  status: number;
  duracao_ms: number;
  linhas: number;
  lote_id: number | null;
  cache: "hit" | "miss";
}

/** Uma linha JSON por requisição (REQ-305). Só parâmetros e contagens; nunca conteúdo de conversa. */
export function formatarLog(l: LinhaLog): string {
  return JSON.stringify({
    request_id: l.request_id,
    endpoint: l.endpoint,
    params: l.params,
    status: l.status,
    duracao_ms: Math.round(l.duracao_ms * 10) / 10,
    linhas: l.linhas,
    lote_id: l.lote_id,
    cache: l.cache,
  });
}

export function formatarServerTiming(bancoMs: number, totalMs: number): string {
  return `db;dur=${bancoMs.toFixed(1)}, total;dur=${totalMs.toFixed(1)}`;
}

export interface ResultadoRota<T> {
  dados: T;
  fonte: string;
  bancoMs: number;
  metaExtra?: Record<string, unknown>;
}

export interface ContextoRota {
  request_id: string;
  params: Record<string, string>;
}

function contarLinhas(dados: unknown): number {
  return Array.isArray(dados) ? dados.length : dados == null ? 0 : 1;
}

/**
 * Embrulha uma rota: gera request_id, mede tempo, monta o envelope com a meta do lote,
 * devolve erros padronizados, põe Server-Timing e escreve a linha de log.
 */
export async function rota<T>(
  endpoint: string,
  req: Request,
  tratar: (ctx: ContextoRota) => Promise<ResultadoRota<T>>,
): Promise<NextResponse> {
  const t0 = performance.now();
  const request_id = novoRequestId();
  const params = Object.fromEntries(new URL(req.url).searchParams.entries());
  let status = 200;
  let linhas = 0;
  let lote_id: number | null = null;
  let bancoMs = 0;
  let corpo: Envelope<T> | ErroApi;

  try {
    const r = await tratar({ request_id, params });
    const m = await lerMeta();
    bancoMs = r.bancoMs + m.ms;
    lote_id = m.meta.lote_id;
    linhas = contarLinhas(r.dados);
    corpo = montarEnvelope(r.dados, { ...m.meta, ...r.metaExtra, request_id, fonte: r.fonte });
  } catch (e) {
    if (e instanceof ErroHttp) {
      status = e.status;
      corpo = montarErro(e.codigo, e.message, request_id);
    } else {
      status = 500;
      corpo = montarErro("ERRO_INTERNO", "Erro interno; informe o request_id.", request_id);
      console.error(JSON.stringify({ request_id, endpoint, erro: e instanceof Error ? e.message : "desconhecido" }));
    }
  }

  const total = performance.now() - t0;
  console.log(formatarLog({ request_id, endpoint, params, status, duracao_ms: total, linhas, lote_id, cache: "miss" }));
  return NextResponse.json(corpo, {
    status,
    headers: { "Server-Timing": formatarServerTiming(bancoMs, total) },
  });
}
