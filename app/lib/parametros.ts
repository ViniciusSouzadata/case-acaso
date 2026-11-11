import { z } from "zod";
import { ErroHttp } from "./api";

const PAISES_CARREGADOS = ["Brazil"] as const;

const dataIso = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "use o formato AAAA-MM-DD")
  .refine((s) => {
    const d = new Date(`${s}T00:00:00Z`);
    return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
  }, "data inexistente");

/** `pais` aceito em todos os endpoints; hoje só Brazil (REQ-308). */
export const pais = z
  .string()
  .default("Brazil")
  .refine((p) => (PAISES_CARREGADOS as readonly string[]).includes(p), "país ainda não carregado");

export const esquemaPais = z.object({ pais });

export const esquemaCoortes = z
  .object({
    pais,
    inicio: dataIso.optional(),
    fim: dataIso.optional(), // exclusivo
    granularidade: z.enum(["semana", "mes"]).default("semana"),
  })
  .refine((p) => !p.inicio || !p.fim || p.inicio <= p.fim, {
    message: "intervalo invertido: inicio deve ser anterior ou igual a fim",
    path: ["inicio"],
  });

const texto = z.string().min(1, "obrigatório").max(80);

export const esquemaEfeitos = z.object({
  pais,
  grupo: z.enum(["assistente", "perfil", "engajamento"]).optional(),
});
export const esquemaSegmentos = z.object({ pais, variavel: texto });
export const esquemaBalanco = z.object({ pais, tratamento: texto });
export const esquemaSemana = z.object({ pais, semana: dataIso });

export const esquemaDicionario = z.object({
  indicador: z.string().min(1).max(80).optional(),
});

/** Valida os parâmetros da query; erro vira 400 PARAMETRO_INVALIDO com mensagem clara. */
export function lerParametros<S extends z.ZodType>(esquema: S, bruto: Record<string, string>): z.infer<S> {
  const r = esquema.safeParse(bruto);
  if (r.success) return r.data;
  const i = r.error.issues[0];
  const campo = i && i.path.length > 0 ? `${i.path.join(".")}: ` : "";
  throw new ErroHttp(400, "PARAMETRO_INVALIDO", `${campo}${i?.message ?? "parâmetro inválido"}`);
}
