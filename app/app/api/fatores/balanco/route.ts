import { rota } from "@/lib/api";
import { esquemaBalanco, lerParametros } from "@/lib/parametros";
import { balanco } from "@/lib/consultas/fatores";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/fatores/balanco", req, async ({ params }) => {
    const p = lerParametros(esquemaBalanco, params);
    const { linhas, ms } = await balanco(p.tratamento);
    return { fonte: "resultado.balanco_propensao", bancoMs: ms, dados: linhas };
  });
}
