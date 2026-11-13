# Requisitos do case — rastreabilidade (fonte: PDF "Desafio Técnico Acaso", 10/11/2026)

> Cada linha é uma exigência literal do PDF. Todo REQ-nnn das features aponta para um C-nn.
> A auditoria final (fase A do BSPA) só fecha quando todas as linhas tiverem evidência.
>
> **T-606, preenchida em 13/11/2026 pelo coordenador.** ✅ = evidência conferida no repositório · 🔶 = depende de passo que ainda não aconteceu (leitura do Vinícius, PDF, envio) · ⬜ = depois do envio.
> Abreviações: `E§n` = seção n de `docs/entrega.md`; `ARQ§n` = seção n de `docs/arquitetura/arquitetura.md`.

| ID | § | Exigência (literal ou quase) | Evidência na entrega | Status |
|----|---|------------------------------|----------------------|--------|
| C-01 | Como funciona | Entrega até seg 16/11 23h59 para nathalia.anjos@aca.so e daniele.cardoso@aca.so | E-mail com PDF + zip (T-605); meta: envio em 13/11 se fechar | 🔶 |
| C-02 | Como funciona | Priorizar decisões claras e justificadas, não documento longo; ~12h esperadas | E§1 (resumo com 3 achados e decisão de cada um); 8 páginas a 11 pt; 10 ADRs + 10 BDRs em `docs/decisoes/`; horas reais em E§13 / `docs/horas.md` | 🔶 (horas) |
| C-03 | Escopo | Análise executada + dashboard funcionando (frontend, backend, base analítica) + doc curto com achados e decisões | `resultado.*` populado por `python -m analise`; app em `app/` (3 telas, 11 rotas); base em `sql/`; `docs/entrega.md`; README em clone limpo (T-603, `docs/gate_m4.md`) | ✅ |
| C-04 | Apresentação | 20 min apresentação + 40 min técnica: fluxo de construção, decisões registradas, o que faria diferente | E§12 (o que faria diferente); ADR/BDR com "Como defender"; roteiro e perguntas em M7 | ⬜ (M7) |
| C-05 | 1 | Pergunta: o que faz voltar em até 7 dias; quais fatores, quanto pesa cada um, quanto é causa × seleção | E§1, E§4 (tabela de efeitos bruto × ajustado; "o que prova e o que não prova"); Tela 2 `/fatores` | ✅ |
| C-06 | 1 | Análise estatística, não só descritiva: efeito com incerteza, separando efeito do assistente do perfil | E§4 (logística com erro agrupado por IP, IPW com balanço, E-value, BH); ADR-10; `analise/`; `resultado.efeito_fator`, `resultado.balanco_propensao` | ✅ |
| C-07 | 1 | Usuário final não técnico; resultados por dashboard (não notebook); cada tela se explica sozinha; cada número com definição e fonte; cada efeito com incerteza | E§6; telas `/`, `/fatores`, `/dados` (capturas em `docs/capturas_m4/`); glossário por número; `mart.dicionario_indicador` | ✅ |
| C-08 | 2 | WildChat-1M, só country = 'Brazil' | `data/bruto/wildchat_brasil.parquet` + `scripts/` de extração (T-102); `docs/discovery/00-resumo-discovery.md`; README "Dados brutos" | ✅ |
| C-09 | 2.1 | Não há ID de usuário: como decidir que duas conversas são da mesma pessoa (avaliado) | E§2 (IP + família do navegador, com sensibilidade só IP / IP+UA); BDR-01; `mart.agg_retencao_sensibilidade` | ✅ |
| C-10 | 2.2 | Dashboard não lê base bruta; base analítica desenhada e populada por você | ARQ§1 e ARQ§5; papel `app_ro` só com SELECT em `mart`/`resultado` (+ `ops.lote_carga`, `ops.reconciliacao`), migrações 001/002/020; varredura de privacidade T-305 | ✅ |
| C-11 | 2.2 | Toda infra e custo do dashboard na AWS, inclusive LLM; análise com qualquer ferramenta; entrega local + descrever implantação | E§7; ARQ§2–3 (US$ 53,50/mês, Price List API 12/11/2026); ADR-08; LLM medido em `docs/custo_llm.md`; entrega local via Docker Compose | ✅ |
| C-12 | 2.2 | Dados pessoais: dizer o que o dashboard mostra e o que nunca mostra | E§6 ("só agregados; nunca texto, IP, user-agent"); BDR-10; ADR-02 (texto fora da base) | ✅ |
| C-13 | 2.3 | Premissas (uso, sessão, fuso, período...): registrar cada uma e o que mudaria se estiver errada | E§2 (tabela com 8 premissas e a taxa recalculada); BDR-01..07 | ✅ |
| C-14 | 3 | Sobe do zero com um comando (ex. docker compose up), carrega base analítica a partir da bruta, ≥2 telas com dados reais | README "Subir do zero"; T-603 em clone limpo (2.372 / 566 / 23,86%); 3 telas; teste do zip em pasta limpa na T-605 | 🔶 (zip) |
| C-15 | 3 | Repositório com instruções + ADRs e BDRs (contexto, opções consideradas, escolha) | `README.md`; `docs/decisoes/` (ADR-01..10, BDR-01..10) | ✅ |
| C-16 | 3.1 | Definição de usuário, sessão, primeira experiência, retorno + quanto o resultado muda se a definição mudar | E§2; BDR-01..04; `ops.parametros`; Tela 1 (pontos de sensibilidade); `mart.agg_retencao_sensibilidade` | ✅ |
| C-17 | 3.1 | Variáveis da 1ª experiência (modelo, tema, tamanho e qualidade da resposta, recusas, turnos, horário, idioma) e derivação de cada uma | E§3 "Variáveis da primeira experiência"; `loader/derivar.py`; `mart.fct_primeira_experiencia`; dicionário na Tela 3 | ✅ |
| C-18 | 3.1 | Se usar IA para classificar, como conferiu o resultado | E§3 "Como conferi a IA" (200 rótulos manuais, kappa, regras × LLM); ADR-09; `docs/validacao_llm.md`, `docs/rotulagem_validacao.md`; `resultado.validacao_classificador` | ✅ |
| C-19 | 3.1 | Problemas de qualidade encontrados e tratamento de cada um | E§3 "Problemas de qualidade"; `resultado.problema_qualidade`; Tela 3 `/dados` | ✅ |
| C-20 | 3.1 | EDA: uso no tempo, por modelo, idioma, tema, tamanho; padrões, concentrações, anomalias; só gráficos que levaram a conclusão | E§3; `docs/figuras/01..06` + `conclusoes.md` (uma frase por gráfico) | ✅ |
| C-21 | 3.1 | O que os dados permitem medir, o que não, e que dados faltam | E§3 "O que dá e o que não dá para medir"; E§1 (efeito mínimo detectável ~5 p.p.) | ✅ |
| C-22 | 3.1 | Sugestões para o assistente (onde falha, temas/respostas que afastam) e para o dashboard (indicadores/telas pensados após ver os dados) | E§11 (assistente e dashboard) | ✅ |
| C-23 | 3.2 | Efeito de cada fator no retorno 7d com IC, ordenado por tamanho | E§4 (tabela); Tela 2 (floresta ordenada, 3 grupos); `/api/fatores/efeitos`; `resultado.efeito_fator` | ✅ |
| C-24 | 3.2 | Fatores de confusão e como tratou (comparar grupos semelhantes); o que prova e o que não prova | E§4 "Fatores de confusão" e "O que prova e o que não prova"; `docs/robustez_recusa.md`; `resultado.balanco_propensao` | ✅ |
| C-25 | 3.2 | Uma semana em que o retorno caiu/subiu e o que explica: mudança de perfil (mix) ou de taxa dentro do perfil | E§5 (20/11/2023 e 01/05/2023, mix × taxa); BDR-09; Tela 1 (cascata); `/api/semana/decomposicao` | ✅ |
| C-26 | 3.2 | Três achados para o cliente e a decisão que cada um sustenta | E§1 (3 achados com decisão e limite); `seeds/achados.yaml` → `resultado.achado`; `/api/achados` | ✅ |
| C-27 | 3.3 | Telas: pergunta que cada uma responde, gráficos e por que esse tipo | E§6 (tabela tela × pergunta × gráfico e por quê) | ✅ |
| C-28 | 3.3 | Indicadores: definição, fórmula, denominador, período de referência, SQL de cada um; o que a tela mostra quando a base é pequena demais | `sql/transform/50_dicionario.sql` → `mart.dicionario_indicador` (com `sql_referencia`); `/api/dicionario`; Tela 3; E§6 "Regra de amostra pequena"; BDR-07 | ✅ |
| C-29 | 3.3 | Arquitetura: fluxo bruto→tela com diagrama; componentes AWS e stack front/back com porquê; modelo da base analítica; endpoints (nome, entrada, saída) | ARQ§1 (diagrama + `fluxo-bruto-tela.png`), ARQ§2–3 (AWS + `implantacao-aws.png`), **ARQ§5 modelo da base e ARQ§6 endpoints (acrescentados em 13/11)**; ADR-01, ADR-06 | ✅ |
| C-30 | 3.3 | Outros países: idioma da interface, fuso de cada país, comparação entre eles | ARQ§4 (país como parâmetro; idioma em `app/mensagens/pt.json`; `fuso_pais`; comparação por mix × taxa); E§7 | ✅ |
| C-31 | 3.3 | Performance: o que é pré-calculado, o que vai para cache, quando expira, como mede tempo de resposta | E§7; ADR-07 (pré-cálculo na carga, cache invalidado por lote); `docs/desempenho.md` (`Server-Timing`, 12 s → 0,33 s) | ✅ |
| C-32 | 4.1 | O que registrar em cada camada (carga, base analítica, backend, tela) para investigar número errado | E§8 "O que registramos em cada camada"; `ops.lote_carga`, `ops.rejeitado`, `ops.reconciliacao`; log JSON com `request_id` (`app/lib/api.ts`) | ✅ |
| C-33 | 4.1 | Como perceber divergência dashboard × base antes do cliente | E§8 "Como perceber a divergência" (reconciliação de 9 métricas a cada carga, 3 regras de alerta) | ✅ |
| C-34 | 4.1 | Testes automatizados que impedem a definição de indicador mudar sem ninguém perceber; caminho até produção (ambientes, migrações, deploy) | E§8 "Testes" e "Caminho até produção"; `tests/esperado.py`, `tests/`; `sql/migrations` + `sql/migrations_down` (12 + 12); `.github/workflows/ci.yml` (configurado, não executado) | ✅ |
| C-35 | 4.2.1 | Incidente: por onde começaria e por quê | E§9 Pergunta 1 | ✅ |
| C-36 | 4.2.2 | Em qual camada está a falha + evidências + consulta para confirmar | E§9 Pergunta 2; `docs/incidente/confirmacao.sql`, `scripts/incidente_confirmacao.py`, `docs/incidente/evidencia.md` | ✅ |
| C-37 | 4.2.3 | Trecho de código que causa + correção escrita | E§9 Pergunta 3; `docs/incidente/correcao/carga_corrigida.py`, `route_corrigida.ts` | ✅ |
| C-38 | 4.2.4 | O que mais fazer além do código + como evitar recorrência | E§9 Pergunta 4; `tests/test_regressao_incidente.py` (T-503) | ✅ |
| C-39 | 4.2.5 | O que dizer à gerente de produto durante e depois | E§9 Pergunta 5 | ✅ |
| C-40 | 4.3 | Riscos principais + decisões a levar ao time/cliente antes de implementar (fora do seu escopo) | E§10 (6 riscos × decisão de quem) | ✅ |
| C-41 | 5 | Parágrafo final: ferramentas de IA e para quê; o que conferiu/corrigiu/descartou; horas aproximadas | E§13; `docs/conferi_da_ia.md`; **horas ainda em "~14 h até 12/11": atualizar com o total do Vinícius** | 🔶 (horas) |
| C-42 | 6 | 8 critérios de avaliação (Análise, Discovery/EDA, Investigação/sustentação, Dashboard, Construção/código, Clareza/premissas, Apresentação, Uso de IA) | Análise: C-05/06/23–26 · Discovery/EDA: C-08/19/20 · Sustentação: C-32–39 · Dashboard: C-07/27/28 · Código: C-14/15/34 · Clareza: C-13/16/21 · Apresentação: C-04 (M7) · IA: C-18/41 | 🔶 (C-04, C-41) |

## Resultado da T-606 (13/11)
- **36 ✅ · 5 🔶 · 1 ⬜.** Os 🔶 fecham com: horas no E§13 (C-02, C-41, C-42), zip testado em pasta limpa (C-14) e envio (C-01). O ⬜ é a M7 (C-04).
- **Lacuna encontrada e corrigida:** o E§7 dizia que o modelo da base estava em `arquitetura.md`, mas não estava; também faltavam os endpoints com entrada e saída (C-29) e o idioma da interface/comparação entre países (C-30). Acrescentados ARQ§5, ARQ§6 e 3 linhas no ARQ§4, conferidos contra `sql/migrations`, `app/app/api/*/route.ts` e `app/lib/mensagens.ts`.
- **Tests da T-606 (revisor independente confere 10 linhas por amostragem):** pendente; vai para a aba Sonnet depois da T-605.
