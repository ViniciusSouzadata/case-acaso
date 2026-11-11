import { rota } from "@/lib/api";
import { ultimoLote } from "@/lib/meta";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/saude", req, async () => {
    const { lote, ms } = await ultimoLote();
    return {
      fonte: "ops.lote_carga",
      bancoMs: ms,
      dados: {
        ok: lote !== null,
        banco: "ok",
        ultimo_lote: lote
          ? {
              lote_id: Number(lote.lote_id),
              terminado_em: lote.terminado_em ? new Date(lote.terminado_em).toISOString() : null,
            }
          : null,
        versao_definicao: lote?.versao_definicao ?? null,
      },
    };
  });
}
