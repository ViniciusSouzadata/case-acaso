import { rota } from "@/lib/api";
import { esquemaEfeitos, lerParametros } from "@/lib/parametros";
import { efeitos } from "@/lib/consultas/fatores";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/fatores/efeitos", req, async ({ params }) => {
    const p = lerParametros(esquemaEfeitos, params);
    const { linhas, ms } = await efeitos(p.grupo);
    return { fonte: "resultado.efeito_fator", bancoMs: ms, dados: linhas };
  });
}
