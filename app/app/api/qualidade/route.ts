import { rota } from "@/lib/api";
import { esquemaPais, lerParametros } from "@/lib/parametros";
import { qualidade } from "@/lib/consultas/qualidade";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return rota("/api/qualidade", req, async ({ params }) => {
    lerParametros(esquemaPais, params);
    const { ms, ...dados } = await qualidade();
    return {
      fonte: "ops.lote_carga; ops.reconciliacao; resultado.problema_qualidade; resultado.validacao_classificador",
      bancoMs: ms,
      dados,
    };
  });
}
