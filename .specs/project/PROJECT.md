# Retenção do Assistente — Case técnico Acaso (Analista de Dados)

> Rascunho v0 (10/11, fase B). Partes marcadas **[pós-perfil]** dependem do perfil dos dados e serão fechadas antes da spec.

## Visão
Responder, para uma empresa dona de um assistente de IA gratuito, **o que faz quem experimentou voltar em até 7 dias**: quais fatores, quanto pesa cada um, com incerteza, e quanto é **causa do assistente** versus **seleção de quem chega**. Os resultados chegam por um **dashboard** que uma pessoa de negócio entende sozinha, sustentado por uma base analítica própria, com a mesma disciplina de sustentação que a Acaso exige em produção.

**Propósito real:** passar na etapa técnica da vaga de Data Analyst Pleno da Acaso e chegar pronto à conversa de 60 min com o gestor (20 apresentação + 40 técnica).

## Interlocutores
| Quem | O que precisa | Como a entrega atende |
|------|---------------|------------------------|
| Cliente (pessoas de negócio, não técnicas) | Saber onde investir; cada número com definição, fonte e incerteza | Telas autoexplicativas, linguagem simples, efeito bruto × ajustado |
| Gerente de produto do cliente (persona do incidente) | Confiar nos números e entender movimentos | Indicadores com ficha, avisos de amostra pequena, coortes imaturas marcadas |
| Avaliadores Acaso (Nathália, Daniele, gestor de dados, diretor técnico) | Rigor estatístico, discovery, código testado, decisões registradas, uso crítico de IA | ADR/BDR com "Como defender", testes, docker compose do zero |

## Princípios inegociáveis
1. **O dashboard nunca lê a base bruta.** Bruto → staging → marts; a tela só lê marts e resultados pré-calculados.
2. **Cada número tem definição, fórmula, denominador, período e fonte** visíveis na tela.
3. **Cada efeito tem incerteza** (IC 95%) e mostra **bruto × ajustado**.
4. **Uma única definição de usuário** para tudo (dashboard, análise, monitoramento) — a lição do incidente §4.2.
5. **Amostra pequena não vira número**: abaixo do mínimo, a tela suprime e explica (vale para estatística e privacidade).
6. **Nunca mostrar** texto de conversa, hashed_ip, user-agent, nem grupos pequenos.
7. **LLM é componente não confiável**: toda classificação por IA é validada contra rótulos manuais e versionada.
8. **Premissa sem sensibilidade não existe**: toda premissa vem com "o que muda se estiver errada".
9. **Método só entra se o Vinícius defende em 40 min.**
10. **Sobe do zero com um comando, sem credencial AWS.**

## Stack (firme)
| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| Extração do bruto | Python 3.12 + DuckDB (lê parquet do Hugging Face / local) | Lê só as colunas/linhas necessárias; rápido em 3,4 GB |
| Base analítica | PostgreSQL 16 | É o que a referência do case usa (SQL do incidente) |
| Transformação + testes de métrica | SQL versionado (migrações numeradas) + pytest com dados de resposta conhecida | Definição de indicador versionada e testada (§4.1) com ferramentas que o Vinícius domina; dbt fica como evolução em ADR |
| Estatística | Python (statsmodels, scikit-learn) gravando resultados em tabelas | Análise com qualquer ferramenta; dashboard só lê |
| Backend + frontend | Next.js (App Router) + TypeScript; rotas de API como na referência | O case sugere; o incidente usa esse stack |
| Orquestração local | Docker Compose (db, loader, app) | Exigência do case |
| Implantação descrita | AWS: S3, ECS Fargate, RDS Postgres, CloudFront, Bedrock, CloudWatch, Secrets Manager **[detalhar no design + custo mensal]** | "Toda infra e custo na AWS" |
| Classificação de tema | **O-01 em aberto** (Bedrock Haiku × local) | — |

## O que NÃO fazer (Lean/MVP)
- Não construir login/multi-tenant, nem deploy real na AWS (só descrito).
- Não exibir nenhum conteúdo de conversa no dashboard.
- Não usar método estatístico que não caiba na explicação de 40 min.
- Não gerar gráfico que não leve a conclusão.
- Não escrever documento longo: detalhe vai para ADR/BDR e anexos.
- Não citar clientes da Acaso (Natura etc.) nem a cultura deles no documento.
- Não superdeclarar experiência (AWS gerenciada e Langfuse são gaps do Vinícius).

## User stories nucleares
- Como **pessoa de negócio**, quero ver a taxa de retorno em 7 dias por semana de chegada, com o que mudou, para saber se estamos melhorando.
- Como **pessoa de negócio**, quero ver quais fatores da primeira experiência mais aumentam ou reduzem o retorno, separando o que é efeito do assistente do que é perfil do usuário, para decidir onde investir.
- Como **gerente de produto**, quero saber quando um número não é confiável (amostra pequena, coorte imatura), para não decidir em cima de ruído.
- Como **time de dados**, quero que dashboard e relatório usem a mesma definição de usuário e que divergências disparem alerta antes do cliente ver.

## Decisões (D-nn) — ver STATE.md para o log
- D-01 Stack acima. D-02 Repo privado + zip. D-03 Compose sem credencial AWS. D-04 Métodos defensáveis. Demais viram ADR/BDR na spec.

## Perguntas em aberto (O-nn)
- O-01 Classificação de tema (Bedrock × local) — Vinícius.
- O-02 **[pós-perfil]** Chave de identidade (IP, IP+UA, IP+família de UA, + filtro de bots).
- O-03 **[pós-perfil]** Definição de sessão (gap de inatividade) e de retorno.
- O-04 **[pós-perfil]** Período analisado (burn-in no início, exclusão de coortes imaturas no fim).
- O-05 **[pós-perfil]** Fuso: America/Sao_Paulo único × fuso por estado.
- O-06 **[pós-perfil]** Semana para a decomposição mix × taxa.

## Contexto da Acaso (uso interno — orienta ênfase, nunca citado)
Startup de Recife, ~35 pessoas, squads (GP, líder técnico, executivo de conta, dados, dev, designer) com responsabilidade ponta a ponta por investigação de falhas e indicadores. Expansão LatAm (México, Argentina, Chile) → a resposta de multi-país (C-30) deve ser concreta. Cultura de autonomia e postura crítica → ser opinativo nas sugestões e nos riscos.
