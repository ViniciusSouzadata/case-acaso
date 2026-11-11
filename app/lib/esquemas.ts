import { z } from "zod";

// Contrato de saída (design.md M3). Estritos: campo a mais, a menos ou de outro tipo quebra o teste de contrato.

export const metaEnvelope = z.object({
  versao_definicao: z.string().nullable(),
  versao_analise: z.string().nullable(),
  atualizado_em: z.string().nullable(),
  lote_id: z.number().int().nullable(),
  request_id: z.string().regex(/^req_[0-9a-f]{6}$/),
  fonte: z.string(),
});

export function envelope<D extends z.ZodType, M extends z.ZodRawShape = Record<string, never>>(
  dados: D,
  metaExtra: M = {} as M,
) {
  return z.strictObject({
    dados,
    meta: z.strictObject({ ...metaEnvelope.shape, ...metaExtra }),
  });
}

export const esquemaErro = z.strictObject({
  erro: z.strictObject({ codigo: z.string(), mensagem: z.string(), request_id: z.string() }),
});

const num = z.number();
const numOuNulo = z.number().nullable();

export const resumoSaida = z.strictObject({
  usuarios: z.number().int(),
  voltaram_7d: z.number().int(),
  taxa: num,
  ic_inf: num,
  ic_sup: num,
  periodo_inicio: z.string().nullable(),
  periodo_fim: z.string().nullable(),
  efeito_minimo_detectavel_pp: num,
});

export const coorteSaida = z.strictObject({
  periodo: z.string(),
  novos: z.number().int(),
  voltaram_7d: z.number().int().nullable(),
  taxa: numOuNulo,
  ic_inf: numOuNulo,
  ic_sup: numOuNulo,
  taxa_mm4: numOuNulo,
  madura: z.boolean(),
  amostra_suficiente: z.boolean(),
});

export const eraSaida = z.strictObject({
  era: z.string(),
  inicio: z.string(),
  fim: z.string().nullable(),
  descricao: z.string(),
});

export const sensibilidadeSaida = z.strictObject({
  definicao: z.string(),
  descricao: z.string(),
  usuarios: z.number().int(),
  voltaram_7d: z.number().int(),
  taxa: num,
  ic_inf: num,
  ic_sup: num,
  delta_vs_oficial: num,
});

export const dicionarioSaida = z.strictObject({
  indicador: z.string(),
  nome_exibicao: z.string(),
  definicao: z.string(),
  formula: z.string(),
  denominador: z.string(),
  periodo_referencia: z.string(),
  fonte: z.string(),
  sql_referencia: z.string(),
  limitacoes: z.string(),
});

export const respostaResumo = envelope(resumoSaida.nullable());
export const respostaCoortes = envelope(z.array(coorteSaida), { eras: z.array(eraSaida) });
export const respostaSensibilidade = envelope(z.array(sensibilidadeSaida));
export const respostaDicionario = envelope(z.array(dicionarioSaida));
