# Incidente §4.2 — raciocínio inicial (rascunho de discovery, a validar com dados)

## O que os números dizem antes de abrir código
| Semana | Dashboard novos | Relatório novos | Δ novos | Dashboard voltaram | Relatório voltaram | Δ voltaram |
|---|---|---|---|---|---|---|
| 06/11 | 1.210 | 1.150 | +60 (+5,2%) | 375 | 345 | +30 |
| 13/11 | 1.188 | 1.131 | +57 (+5,0%) | 368 | 351 | +17 |
| 20/11 | 2.034 | 1.172 | **+862 (+73,5%)** | 366 | 352 | +14 |

- O **numerador** (voltaram) é estável nas duas fontes; o **denominador** (novos) explode só no dashboard. → problema de **contagem de usuários novos**, não de retorno.
- Diferença de ~5% em semanas normais → as duas fontes **sempre** discordaram: definições de usuário diferentes (relatório: `hashed_ip`; carga: `sha256(hashed_ip|user-agent)`).
- IC 95% de 31% com n≈1.200 ≈ ±2,6 p.p. → 31%→30% é ruído; 31%→18% não é.

## Hipóteses (todas compatíveis com "mais novos, mesmos retornos")
| H | Mecanismo | Previsão testável no bruto |
|---|---|---|
| H1 | Um/poucos IPs com user-agent rotativo (bot, scraper, cliente que randomiza UA) | Poucos IPs concentram centenas de UAs novos na semana; cada UA com 1 conversa; horários regulares; volume anormal |
| H2 | IP compartilhado (CGNAT, escola, empresa) com muitas pessoas novas de verdade | Muitos UAs distintos por IP, mas UAs "comuns", horários humanos; pode persistir em outras semanas |
| H3 | Usuários existentes trocaram de UA (atualização de navegador — gatilho mais comum e provavelmente o cenário imaginado pelo autor do case) | Novos IDs em IPs já vistos antes, com UA diferindo só na versão. Ressalva: esses usuários tenderiam a voltar, então voltaram_7d também deveria subir — a consulta mostra se foi isso |

> Em qualquer das três, a causa-raiz é a mesma linha: `chave = f"{hashed_ip}|{user-agent}"`. As hipóteses só explicam o gatilho daquela semana.
| H4 | Carga duplicada/reprocessada | Descartada como causa principal: `ON CONFLICT (conversa_id) DO NOTHING` impede linha duplicada; e duplicar conversa não cria usuário novo |

## Camada da falha
**Carga** (definição de `usuario_id`), propagada para a base analítica. O endpoint calcula corretamente sobre o que recebe; a tela só exibe. A base bruta é a mesma do relatório (que está estável).

## Consulta de confirmação (bruto)
```sql
-- novos por chave IP+UA cujo IP já existia; concentração de UAs novos por IP, por semana
WITH f AS (
  SELECT hashed_ip, header->>'user-agent' AS ua, min("timestamp") AS t0
  FROM bruto.conversas WHERE country = 'Brazil' GROUP BY 1, 2
)
SELECT date_trunc('week', t0) AS semana, hashed_ip, count(*) AS uas_novos
FROM f
WHERE t0 >= '2023-11-06' AND t0 < '2023-11-27'
GROUP BY 1, 2
ORDER BY uas_novos DESC
LIMIT 20;
```

## Outros defeitos no código de referência (mesmo sem relação direta com a queda)
1. `primeira_vez = min(ultimo_turno)` — usa o **último** turno como "primeira vez"; deveria usar o início da conversa.
2. Coortes **imaturas** não são marcadas: quem chegou nos últimos 7 dias do período ainda não teve janela completa.
3. `date_trunc('week', ...)` no fuso da sessão do banco (UTC) — semana do cliente é no fuso local.
4. `ON CONFLICT DO NOTHING` congela conversas que continuam em outro dia (turnos, último turno ficam velhos) → deveria ser upsert idempotente.
5. Filtro `pais = $3` só na CTE `primeira`; retorno em outro país conta (aceitável, mas tem de ser decisão explícita).
6. Inserção linha a linha, sem transação nem log de lote → carga parcial silenciosa.
7. Raiz organizacional: **duas definições de usuário** (relatório × dashboard) e nenhuma reconciliação automática.

## Correção (direção)
- Uma tabela `dim_usuario` com a regra oficial de identidade (a decidir no O-02) + filtro de tráfego automatizado, usada por dashboard e relatório.
- Carga com upsert, transação por lote, registro de lote (linhas lidas/gravadas/rejeitadas).
- Endpoint com início da conversa, coortes imaturas marcadas, semana no fuso do país.
- Reprocessar o histórico (backfill) e versionar a mudança de definição.

## Prevenção
- Reconciliação diária bruto × marts (novos e voltaram por semana) com tolerância e alerta.
- Alerta de anomalia em "novos por semana" e em "UAs por IP".
- Testes dbt com dados sintéticos de resposta conhecida (inclui caso de UA rotativo).

## Comunicação à gerente de produto
- **Durante:** "A queda é quase certamente de medição, não de comportamento: o número de quem voltou não mudou, só o de quem chegou. Não tome decisão em cima do 18%. Volto em X horas com a confirmação."
- **Depois:** causa em uma frase, número corrigido com intervalo, o que mudou na contagem, o que impede de repetir, e que semanas anteriores tinham ~5% de viés que também foi corrigido.
