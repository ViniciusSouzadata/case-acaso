# ROADMAP — case Acaso

Entrega: seg 16/11/2026 (meta: à tarde). Régua de aceite: `CASE-REQUIREMENTS.md` (C-01..C-42).

## Milestones
| # | Milestone | O que entrega | Cobre | Gate de saída | Quando |
|---|-----------|---------------|-------|---------------|--------|
| M0 | Discovery | Extrato Brasil, perfil, decisões de definição | C-08, C-09, C-16, C-19 (parcial) | `docs/discovery/00-resumo-discovery.md` + decisões no STATE ✅ | ter 10 ✅ |
| M1 | Base analítica | Carga bruto→staging→marts em Postgres; identidade, sessões, 1ª experiência, retorno; variáveis; tema (seed); log de carga; compose `db`+`loader` | C-10, C-14 (parte), C-16, C-17, C-18, C-19 | `docker compose up` popula a base do zero; testes de métrica verdes; contagens batem com o discovery (11.621 conversas; retorno ~24%) | qui 12 |
| M2 | Análise | EDA (só gráficos com conclusão), efeitos bruto × ajustado com IC, confusão, semana 20/11/2023 (mix × taxa), sensibilidades, 3 achados; resultados gravados em tabelas | C-05, C-06, C-13, C-20..C-26 | Tabelas `resultado_*` populadas e reproduzíveis por um comando; cada efeito com IC e n | sex 13 |
| M3 | Backend | Rotas de API (Next.js/TS) lendo só marts/resultados; validação de parâmetros; cache; log com request_id e duração | C-10, C-29, C-31, C-32 | Contratos de `design.md` atendidos; testes de contrato verdes; p95 medido | sex 13 |
| M4 | Frontend | Telas **Retenção** e **Fatores** (+ **Qualidade dos dados** se couber); glossário por número; aviso de amostra pequena e coorte imatura | C-07, C-12, C-14, C-27, C-28 | Pessoa não técnica entende cada tela sem ajuda (checklist); 2+ telas com dados reais | sáb 14 |
| M5 | Sustentação | Reconciliação bruto × marts, testes de definição, descrição de ambientes/migrações/deploy, incidente §4.2 completo | C-32..C-39 | As 5 perguntas do incidente respondidas com consulta e correção escritas; teste que falha se a definição mudar | sáb 14 |
| M6 | Documento | Doc curto (achados, decisões, premissas, arquitetura AWS + custo, multi-país, riscos §4.3, parágrafo de IA), ADRs/BDRs, README | C-02, C-03, C-11, C-12, C-13, C-15, C-29, C-30, C-40, C-41 | Todas as linhas C-nn com evidência; doc ≤ ~8 páginas | dom 15 |
| A | Auditoria | Revisão em ciclos por revisor separado; compose do zero em pasta limpa; matriz C-nn fechada | C-42 | Zero pendência crítica/importante | dom 15 – seg 16 |
| M7 | Prep da apresentação | Roteiro 20 min, banco de perguntas 40 min, armadilhas, quiz | C-04 | Vinícius explica cada decisão sem consultar | após envio |

## Regras de sequência
1. M1 é caminho crítico: **esquema da base e contratos de API congelam antes de paralelizar** M2‖M3‖M4‖M5.
2. M3 e M4 podem começar com dados de exemplo no formato do contrato; trocam para dados reais quando M2 gravar os resultados.
3. Nada entra em M4 que não tenha definição + fonte + incerteza prontas em M1/M2.
4. Cada agente Sonnet trabalha em worktree próprio, recebe **uma** task e os caminhos de spec/design; integração e revisão ficam com o modelo de planejamento.
5. Commits locais a cada gate de milestone.

## Prioridade (corte se o tempo apertar)
- **Must:** M1, M2, M3, telas Retenção e Fatores (M4), incidente (M5), M6, Auditoria.
- **Should:** tela Qualidade dos dados, reconciliação automática rodando, tema via Bedrock, cache + medição de p95.
- **Could:** alternar pt/es na interface, CI (GitHub Actions), esqueleto de IaC.
- **Não fazer:** deploy real na AWS, login, qualquer exibição de conteúdo de conversa.

## Riscos
| Risco | Efeito | Mitigação |
|-------|--------|-----------|
| Docker não instalado / virtualização desligada | Sem entrega | Instalar hoje; se falhar, diagnosticar BIOS/WSL amanhã cedo |
| Conta AWS nova demora a liberar Claude no Bedrock | Tema atrasa | Amazon Nova como reserva na AWS; classificador local como última reserva; tema é Should |
| Base pequena (2.385 usuários, ~577 retornos) | ICs largos; poucos efeitos "significativos" | Dizer isso com clareza (efeito mínimo detectável ~5–7 p.p.); limitar parâmetros; não vender ruído como achado |
| Modelo confundido com tempo (GPT-4 indisponível jul–out/2023) | Efeito de modelo enviesado | Comparar dentro do período; efeito fixo de período; reportar como limite |
| Identidade por IP (CGNAT, IP dinâmico) | Retorno sub/superestimado | Sensibilidade com 3 chaves; registrar como limite e dado que falta (ID de login) |
| Vinícius não conseguir defender uma decisão | Entrevista | Só ferramentas/métodos que ele domina; "Como defender" em cada ADR; M7 |
| Escopo maior que o tempo | Entrega incompleta | Corte Must/Should/Could; esqueleto ponta a ponta primeiro |
| Agentes paralelos divergirem | Retrabalho | Contratos congelados; worktrees; integração centralizada |
