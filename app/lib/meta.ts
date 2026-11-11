import { consultar } from "./db";

export interface MetaBase {
  versao_definicao: string | null;
  versao_analise: string | null; // null enquanto resultado.meta estiver vazio (M2 ainda não rodou)
  atualizado_em: string | null;
  lote_id: number | null;
}

interface LinhaLote {
  lote_id: string;
  versao_definicao: string | null;
  terminado_em: Date | null;
}

/** Último lote carregado com sucesso (ops.lote_carga). */
export async function ultimoLote(): Promise<{ lote: LinhaLote | null; ms: number }> {
  const { linhas, ms } = await consultar<LinhaLote>(
    `SELECT lote_id, versao_definicao, terminado_em
       FROM ops.lote_carga WHERE status = 'sucesso'
      ORDER BY lote_id DESC LIMIT 1`,
  );
  return { lote: linhas[0] ?? null, ms };
}

/** Versão da análise gravada pelo M2; null se ainda não há linha. */
export async function versaoAnalise(): Promise<{ versao: string | null; ms: number }> {
  const { linhas, ms } = await consultar<{ versao_analise: string }>(
    `SELECT versao_analise FROM resultado.meta ORDER BY executado_em DESC LIMIT 1`,
  );
  return { versao: linhas[0]?.versao_analise ?? null, ms };
}

export async function lerMeta(): Promise<{ meta: MetaBase; ms: number }> {
  const [l, a] = await Promise.all([ultimoLote(), versaoAnalise()]);
  return {
    meta: {
      versao_definicao: l.lote?.versao_definicao ?? null,
      versao_analise: a.versao,
      atualizado_em: l.lote?.terminado_em ? new Date(l.lote.terminado_em).toISOString() : null,
      lote_id: l.lote ? Number(l.lote.lote_id) : null,
    },
    ms: l.ms + a.ms,
  };
}
