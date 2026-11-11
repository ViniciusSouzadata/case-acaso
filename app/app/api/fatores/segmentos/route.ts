import { rota } from "@/lib/api";
import { esquemaSegmentos, lerParametros } from "@/lib/parametros";
import { segmentos } from "@/lib/consultas/fatores";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/fatores/segmentos", req, async ({ params }) => {
    const p = lerParametros(esquemaSegmentos, params);
    const { linhas, ms } = await segmentos(p.variavel);
    return { fonte: "mart.agg_retencao_segmento", bancoMs: ms, dados: linhas };
  });
}
