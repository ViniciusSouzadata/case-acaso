import { rota } from "@/lib/api";
import { esquemaCoortes, lerParametros } from "@/lib/parametros";
import { coortes, eras } from "@/lib/consultas/retencao";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/retencao/coortes", req, async ({ params }) => {
    const p = lerParametros(esquemaCoortes, params);
    const [c, e] = await Promise.all([coortes(p.granularidade, p.inicio, p.fim), eras()]);
    return {
      fonte: "mart.agg_retencao_periodo",
      bancoMs: c.ms + e.ms,
      dados: c.linhas,
      metaExtra: { eras: e.linhas },
    };
  });
}
