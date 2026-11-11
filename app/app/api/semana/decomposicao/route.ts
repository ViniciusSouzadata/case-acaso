import { rota } from "@/lib/api";
import { esquemaSemana, lerParametros } from "@/lib/parametros";
import { decomposicao } from "@/lib/consultas/semana";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/semana/decomposicao", req, async ({ params }) => {
    const p = lerParametros(esquemaSemana, params);
    const { resumo, segmentos, ms } = await decomposicao(p.semana);
    return {
      fonte: "resultado.decomposicao_resumo; resultado.decomposicao_semana",
      bancoMs: ms,
      dados: { resumo, segmentos },
    };
  });
}
