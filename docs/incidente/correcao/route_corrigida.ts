// Correção escrita do endpoint de retenção (incidente §4.2). Código de documentação: autocontido (sem imports do projeto),
// compila em modo estrito, não roda sozinho. Cada correção tem um comentário "DEFEITO:" dizendo o que resolve.

/** Contrato mínimo do acesso ao banco (o projeto usa `consultar` de lib/db.ts, com o papel somente leitura). */
export interface Banco {
  consultar<T>(sql: string, parametros: ReadonlyArray<string | number | null>): Promise<T[]>;
}

export interface Coorte {
  semana: string; // início da semana no fuso do país (segunda-feira)
  novos: number;
  voltaram_7d: number;
  taxa: number | null;
  madura: boolean; // false: algum usuário da semana ainda não tem a janela de 7 dias completa
}

const FUSO_DO_PAIS = "America/Sao_Paulo";

// DEFEITO 1: o código de referência montava a identidade aqui (`${hashed_ip}|${user_agent}`). Agora o usuário vem pronto de
// mart.dim_usuario, que usa a mesma regra do relatório do time de dados (uma definição, versionada).
// DEFEITO 2: "primeira vez" era o ÚLTIMO turno da conversa; agora é o início da primeira sessão do usuário (dim_usuario.ts_primeira).
// DEFEITO 3: date_trunc('week', ...) rodava no fuso da sessão do banco (UTC); agora a semana é no fuso do país.
// DEFEITO 4: coortes dos últimos 7 dias não tinham janela completa e apareciam como queda; agora vêm marcadas (maduro = false).
// DEFEITO 5: o filtro de país só valia na CTE da primeira vez. Aqui o recorte de país é decisão explícita e única: o mart já é
// só do país (Brasil), então não há segundo filtro, e o retorno de quem mudou de país não é descartado em silêncio.
const SQL_COORTES = `
  SELECT date_trunc('week', u.ts_primeira AT TIME ZONE '${FUSO_DO_PAIS}')::date::text AS semana,
         count(*) FILTER (WHERE u.elegivel)::int AS novos,
         count(*) FILTER (WHERE u.elegivel AND f.voltou_7d)::int AS voltaram_7d,
         bool_and(u.maduro) AS madura
    FROM mart.dim_usuario u
    LEFT JOIN mart.fct_primeira_experiencia f USING (usuario_id)
   WHERE u.ts_primeira >= $1::timestamptz
     AND u.ts_primeira <  $2::timestamptz
   GROUP BY 1
   ORDER BY 1
`;

interface LinhaCoorte {
  semana: string;
  novos: number;
  voltaram_7d: number;
  madura: boolean;
}

export async function coortesDeRetencao(
  banco: Banco,
  inicio: Date,
  fim: Date,
): Promise<Coorte[]> {
  const linhas = await banco.consultar<LinhaCoorte>(SQL_COORTES, [inicio.toISOString(), fim.toISOString()]);
  return linhas.map((l) => ({
    semana: l.semana,
    novos: l.novos,
    voltaram_7d: l.voltaram_7d,
    // DEFEITO 4 (continuação): coorte imatura não ganha taxa; a tela mostra "ainda sem janela completa", não uma queda.
    taxa: l.madura && l.novos > 0 ? l.voltaram_7d / l.novos : null,
    madura: l.madura,
  }));
}

/** Resposta do endpoint: junta a coorte com a versão da definição, para o rodapé da tela e a reconciliação saberem qual regra gerou o número. */
export async function respostaRetencao(
  banco: Banco,
  inicio: Date,
  fim: Date,
): Promise<{ versao_definicao: string; coortes: Coorte[] }> {
  const [v] = await banco.consultar<{ versao_definicao: string }>(
    "SELECT versao_definicao FROM resultado.meta ORDER BY executado_em DESC LIMIT 1",
    [],
  );
  return { versao_definicao: v?.versao_definicao ?? "desconhecida", coortes: await coortesDeRetencao(banco, inicio, fim) };
}
