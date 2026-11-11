import { rota } from "@/lib/api";
import { esquemaDicionario, lerParametros } from "@/lib/parametros";
import { dicionario } from "@/lib/consultas/dicionario";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/dicionario", req, async ({ params }) => {
    const p = lerParametros(esquemaDicionario, params);
    const { linhas, ms } = await dicionario(p.indicador);
    return { fonte: "mart.dicionario_indicador", bancoMs: ms, dados: linhas };
  });
}
