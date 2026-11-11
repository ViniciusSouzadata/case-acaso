import { rota } from "@/lib/api";
import { esquemaPais, lerParametros } from "@/lib/parametros";
import { sensibilidade } from "@/lib/consultas/retencao";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/retencao/sensibilidade", req, async ({ params }) => {
    lerParametros(esquemaPais, params);
    const { linhas, ms } = await sensibilidade();
    return { fonte: "mart.agg_retencao_sensibilidade", bancoMs: ms, dados: linhas };
  });
}
