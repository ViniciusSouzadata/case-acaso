import { rota } from "@/lib/api";
import { esquemaPais, lerParametros } from "@/lib/parametros";
import { achados } from "@/lib/consultas/qualidade";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/achados", req, async ({ params }) => {
    lerParametros(esquemaPais, params);
    const { linhas, ms } = await achados();
    return { fonte: "resultado.achado", bancoMs: ms, dados: linhas };
  });
}
