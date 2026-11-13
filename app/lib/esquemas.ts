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
  inicio_coleta: z.boolean(),
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

// ---- T-303: fatores, semana, achados, qualidade
export const efeitoSaida = z.strictObject({
  fator: z.string(),
  nivel: z.string(),
  referencia: z.string(),
  grupo: z.enum(["assistente", "perfil", "engajamento"]),
  n_nivel: z.number().int(),
  n_referencia: z.number().int(),
  taxa_nivel: numOuNulo,
  taxa_referencia: numOuNulo,
  efeito_bruto_pp: numOuNulo,
  bruto_ic_inf: numOuNulo,
  bruto_ic_sup: numOuNulo,
  efeito_ajustado_pp: numOuNulo,
  ajustado_ic_inf: numOuNulo,
  ajustado_ic_sup: numOuNulo,
  p_valor: numOuNulo,
  significativo_fdr: z.boolean().nullable(),
  e_value: numOuNulo,
  metodo: z.enum(["logit_ame", "ipw"]),
  amostra_suficiente: z.boolean(),
  leitura: z.string().nullable(),
  ordem: z.number().int().nullable(),
});

export const segmentoSaida = z.strictObject({
  valor: z.string(),
  novos: z.number().int(),
  voltaram_7d: z.number().int(),
  taxa: num,
  ic_inf: num,
  ic_sup: num,
  amostra_suficiente: z.boolean(),
});

export const balancoSaida = z.strictObject({
  covariavel: z.string(),
  dp_antes: numOuNulo,
  dp_depois: numOuNulo,
});

export const resumoSemanaSaida = z.strictObject({
  semana: z.string(),
  base_descricao: z.string().nullable(),
  n_base: z.number().int().nullable(),
  n_semana: z.number().int().nullable(),
  taxa_base: numOuNulo,
  taxa_semana: numOuNulo,
  delta_pp: numOuNulo,
  mix_pp: numOuNulo,
  taxa_pp: numOuNulo,
  p_valor: numOuNulo,
  conclusao: z.string().nullable(),
});

export const segmentoSemanaSaida = z.strictObject({
  semana: z.string(),
  segmento: z.string(),
  peso_base: numOuNulo,
  peso_semana: numOuNulo,
  taxa_base: numOuNulo,
  taxa_semana: numOuNulo,
  efeito_mix_pp: numOuNulo,
  efeito_taxa_pp: numOuNulo,
});

export const achadoSaida = z.strictObject({
  ordem: z.number().int(),
  titulo: z.string(),
  evidencia: z.string(),
  decisao: z.string(),
  limite: z.string(),
  // opcionais (migração 012): cartão curto da Tela 2
  numero_destaque: z.string().nullable(),
  rotulo_destaque: z.string().nullable(),
  acao_curta: z.string().nullable(),
});

export const qualidadeSaida = z.strictObject({
  lote: z
    .strictObject({
      lote_id: z.number().int(),
      iniciado_em: z.string(),
      terminado_em: z.string().nullable(),
      fonte: z.string().nullable(),
      linhas_lidas: z.number().int().nullable(),
      linhas_gravadas: z.number().int().nullable(),
      linhas_rejeitadas: z.number().int().nullable(),
      versao_definicao: z.string().nullable(),
      status: z.string(),
    })
    .nullable(),
  reconciliacao: z.array(
    z.strictObject({
      metrica: z.string(),
      valor_bruto: numOuNulo,
      valor_mart: numOuNulo,
      diferenca: numOuNulo,
      tolerancia: numOuNulo,
      ok: z.boolean(),
    }),
  ),
  problemas: z.array(
    z.strictObject({
      problema: z.string(),
      contagem: z.number().int(),
      percentual: numOuNulo,
      tratamento: z.string().nullable(),
    }),
  ),
  validacao: z.array(
    z.strictObject({
      classificador: z.string(),
      n: z.number().int(),
      acuracia: numOuNulo,
      kappa: numOuNulo,
      detalhe_json: z.unknown(),
      versao_prompt: z.string().nullable(),
      modelo: z.string().nullable(),
    }),
  ),
});

export const respostaEfeitos = envelope(z.array(efeitoSaida));
export const respostaSegmentos = envelope(z.array(segmentoSaida));
export const respostaBalanco = envelope(z.array(balancoSaida));
export const respostaSemana = envelope(
  z.strictObject({ resumo: resumoSemanaSaida.nullable(), segmentos: z.array(segmentoSemanaSaida) }),
);
export const respostaAchados = envelope(z.array(achadoSaida));
export const respostaQualidade = envelope(qualidadeSaida);
