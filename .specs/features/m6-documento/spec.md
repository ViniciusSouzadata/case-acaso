# M6 — Documento, decisões e README

## Objetivo
Um documento curto que o avaliador lê em 15 minutos e que responde, na ordem do case, a tudo que foi pedido — com o detalhe nos ADRs/BDRs e no repositório.

## Estrutura do documento (`docs/entrega.md` → PDF; alvo ≤ 8 páginas + anexos)
1. **Resumo em 5 linhas**: resposta à pergunta de negócio + os 3 achados com a decisão de cada um.
2. **Definições e premissas** (tabela): premissa, escolha, o que muda no resultado se estiver errada (com o número recalculado).
3. **O que os dados mostram** (EDA): só os gráficos com conclusão; problemas de qualidade e tratamento; o que dá e o que não dá para medir; dados que faltam.
4. **Efeitos**: tabela ordenada, bruto × ajustado, IC; confusão e como foi tratada; o que prova e o que não prova.
5. **A semana de 20/11/2023**: mix × taxa e o veredito sobre ruído.
6. **Dashboard**: telas (pergunta, gráfico, porquê); ficha dos indicadores (definição, fórmula, denominador, período, SQL); regra de amostra pequena; o que mostra e o que nunca mostra.
7. **Arquitetura**: diagrama bruto → tela; modelo da base; endpoints; componentes AWS com porquê e **custo mensal estimado**; implantação; outros países (idioma, fuso, comparação); desempenho (pré-cálculo, cache, expiração, medição).
8. **Sustentação**: registros por camada, detecção de divergência, testes de definição, caminho até produção.
9. **Incidente**: as 5 respostas.
10. **Riscos e decisões a escalar**.
11. **Sugestões** para o assistente e para o dashboard.
12. **Uso de IA** (parágrafo): ferramentas e para quê; o que foi conferido, corrigido, descartado; horas.

## Requirements
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-601 | Documento segue a estrutura acima e cada seção cita o C-nn que responde | Crítica | C-02, C-03 |
| REQ-602 | ADRs e BDRs em `docs/decisoes/` no formato: Contexto · Opções consideradas · Escolha · Consequências · **Como defender** (por que, o que descartei, o que mudaria minha decisão, o que faria diferente) | Crítica | C-15, C-04 |
| REQ-603 | README: pré-requisitos, **um comando** para subir, o que esperar em cada serviço, como rodar testes, como refazer do bruto completo, estrutura do repositório | Crítica | C-14, C-15 |
| REQ-604 | Arquitetura AWS dimensionada ao tamanho real: S3 (bruto), ECS Fargate agendado (carga + análise), RDS PostgreSQL, App Runner ou ECS (app), CloudFront, Bedrock, CloudWatch, Secrets Manager; diagrama; custo mensal por componente | Crítica | C-11, C-29 |
| REQ-605 | Seção de outros países concreta: mensagens por idioma, fuso por país/estado em parâmetro, coorte no horário local, comparação padronizada pelo mix, carga por país | Crítica | C-30 |
| REQ-606 | Riscos e decisões a escalar: definição oficial de usuário (precisa de ID de login), política de retenção de dados e LGPD, orçamento de LLM, quem aprova mudança de definição, SLA de atualização | Crítica | C-40 |
| REQ-607 | Parágrafo de IA honesto, com as horas reais registradas em `docs/horas.md` | Crítica | C-41 |
| REQ-608 | Nenhuma afirmação de experiência que o Vinícius não tem; nada sobre clientes da Acaso | Crítica | — |
| REQ-609 | `CASE-REQUIREMENTS.md` com a coluna "Evidência" preenchida para as 42 linhas | Crítica | C-42 |

## Lista completa de decisões a registrar (auditoria S.5)
BDR-01 usuário · BDR-02 sessão e retorno · BDR-03 o que conta como uso · BDR-04 burn-in e coortes imaturas · BDR-05 tráfego anômalo · BDR-06 fuso · BDR-07 n mínimo e supressão · BDR-08 fatores em 3 grupos (assistente/perfil/engajamento) · BDR-09 semana analisada · BDR-10 o que o painel mostra e nunca mostra.
ADR-01 Postgres + reconstrução completa · ADR-02 texto fora da base · ADR-03 SQL versionado + pytest (dbt como evolução) · ADR-04 snapshot + FULL_REFRESH · ADR-05 parâmetros versionados · ADR-06 Next.js com rotas de API (× backend separado) · ADR-07 pré-cálculo + cache por lote · ADR-08 arquitetura AWS e custo · ADR-09 classificação de tema (Bedrock × alternativa, conforme resposta da Acaso) · ADR-10 método estatístico.

## Gate de saída
Matriz C-01..C-42 com evidência; documento ≤ 8 páginas; leitura a frio por revisor separado sem dúvida crítica.
