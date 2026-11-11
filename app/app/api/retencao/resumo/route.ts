import { rota } from "@/lib/api";
import { esquemaPais, lerParametros } from "@/lib/parametros";
import { resumo } from "@/lib/consultas/retencao";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/retencao/resumo", req, async ({ params }) => {
    lerParametros(esquemaPais, params);
    const { linhas, ms } = await resumo();
    return { fonte: "resultado.meta", bancoMs: ms, dados: linhas[0] ?? null };
  });
}
