# Requisitos do case — rastreabilidade (fonte: PDF "Desafio Técnico Acaso", 10/11/2026)

> Cada linha é uma exigência literal do PDF. Todo REQ-nnn das features aponta para um C-nn.
> A auditoria final (fase A do BSPA) só fecha quando todas as linhas tiverem evidência.
>
> **Preenchida em 13/11/2026 e revista em 15/11/2026, no fechamento.** ✅ = evidência conferida no repositório · 🔶 = depende de passo que ainda não aconteceu (leitura do Vinícius, PDF, envio) · ⬜ = depois do envio.
> Abreviações: `E§n` = seção n de `docs/entrega.md` (numeração final); `E-resumo` = primeira página; `ARQ§n` = seção n de `docs/arquitetura/arquitetura.md`.

| ID | § | Exigência (literal ou quase) | Evidência na entrega | Status |
|----|---|------------------------------|----------------------|--------|
| C-01 | Como funciona | Entrega até seg 16/11 23h59 para nathalia.anjos@aca.so e daniele.cardoso@aca.so | E-mail com `docs/entrega.pdf` e `dist/case_acaso.zip`, enviado pelo Vinícius | 🔶 (envio) |
| C-02 | Como funciona | Priorizar decisões claras e justificadas, não documento longo; ~12h esperadas | E-resumo (resumo com 3 achados e decisão de cada um); PDF de 7 páginas; 10 ADRs + 10 BDRs em `docs/decisoes/`; horas reais em E§11 / `docs/horas.md` | ✅ |
| C-03 | Escopo | Análise executada + dashboard funcionando (frontend, backend, base analítica) + doc curto com achados e decisões | `resultado.*` populado por `python -m analise`; app em `app/` (3 telas, 11 rotas); base em `sql/`; `docs/entrega.md`; README em clone limpo (T-603, `docs/gate_m4.md`) | ✅ |
| C-04 | Apresentação | 20 min apresentação + 40 min técnica: fluxo de construção, decisões registradas, o que faria diferente | Fica para a fala (saiu do PDF em 15/11, o enunciado pede na apresentação); ADR/BDR com "Como defender"; roteiro e perguntas em M7 | ⬜ (M7) |
| C-05 | 1 | Pergunta: o que faz voltar em até 7 dias; quais fatores, quanto pesa cada um, quanto é causa × seleção | E-resumo, E§3 (tabela de efeitos bruto × ajustado; "o que prova e o que não prova"); Tela 2 `/fatores` | ✅ |
| C-06 | 1 | Análise estatística, não só descritiva: efeito com incerteza, separando efeito do assistente do perfil | E§3 (logística com erro agrupado por IP, IPW com balanço, E-value, BH); ADR-10; `analise/`; `resultado.efeito_fator`, `resultado.balanco_propensao` | ✅ |
| C-07 | 1 | Usuário final não técnico; resultados por dashboard (não notebook); cada tela se explica sozinha; cada número com definição e fonte; cada efeito com incerteza | E§5; telas `/`, `/fatores`, `/dados` (capturas em `docs/capturas_m4/`); caixa de detalhe por número, com bloco técnico; `mart.dicionario_indicador` | ✅ |
| C-08 | 2 | WildChat-1M, só country = 'Brazil' | `data/bruto/wildchat_brasil.parquet` + `scripts/` de extração (T-102); `docs/discovery/00-resumo-discovery.md`; README "Dados brutos" | ✅ |
| C-09 | 2.1 | Não há ID de usuário: como decidir que duas conversas são da mesma pessoa (avaliado) | E§1 (IP + família do navegador, com sensibilidade só IP / IP+UA); BDR-01; `mart.agg_retencao_sensibilidade` | ✅ |
| C-10 | 2.2 | Dashboard não lê base bruta; base analítica desenhada e populada por você | ARQ§1 e ARQ§5; papel `app_ro` só com SELECT em `mart`/`resultado` (+ `ops.lote_carga`, `ops.reconciliacao`), migrações 001/002/020; varredura de privacidade T-305 | ✅ |
| C-11 | 2.2 | Toda infra e custo do dashboard na AWS, inclusive LLM; análise com qualquer ferramenta; entrega local + descrever implantação | E§6; ARQ§2–3 (US$ 53,50/mês, Price List API 12/11/2026); ADR-08; LLM medido em `docs/custo_llm.md`; entrega local via Docker Compose | ✅ |
| C-12 | 2.2 | Dados pessoais: dizer o que o dashboard mostra e o que nunca mostra | E§5 ("só agregados; nunca texto, IP, user-agent"); BDR-10; ADR-02 (texto fora da base) | ✅ |
| C-13 | 2.3 | Premissas (uso, sessão, fuso, período...): registrar cada uma e o que mudaria se estiver errada | E§1 (tabela com 8 premissas e a taxa recalculada); BDR-01..07 | ✅ |
| C-14 | 3 | Sobe do zero com um comando (ex. docker compose up), carrega base analítica a partir da bruta, ≥2 telas com dados reais | README "Subir do zero"; T-603 em clone limpo (2.372 / 566 / 23,86%); 3 telas; zip testado em pasta limpa em 15/11 (9/9, 2.372 / 566 / 23,86%); em máquina com 4 GB, subir em etapas (README) | ✅ |
| C-15 | 3 | Repositório com instruções + ADRs e BDRs (contexto, opções consideradas, escolha) | `README.md`; `docs/decisoes/` (ADR-01..10, BDR-01..10); o zip é o repositório git com o histórico (`git log`) | ✅ |
| C-16 | 3.1 | Definição de usuário, sessão, primeira experiência, retorno + quanto o resultado muda se a definição mudar | E§1; BDR-01..04; `ops.parametros`; Tela 1 (cartão "Se mudar a forma de contar"); `mart.agg_retencao_sensibilidade` | ✅ |
| C-17 | 3.1 | Variáveis da 1ª experiência (modelo, tema, tamanho e qualidade da resposta, recusas, turnos, horário, idioma) e derivação de cada uma | E§2 "Variáveis da primeira experiência"; `loader/derivar.py`; `mart.fct_primeira_experiencia`; dicionário na Tela 3 | ✅ |
| C-18 | 3.1 | Se usar IA para classificar, como conferiu o resultado | E§2 "Como conferi a IA" (200 rótulos manuais, kappa, regras × LLM); ADR-09; `docs/validacao_llm.md`, `docs/rotulagem_validacao.md`; `resultado.validacao_classificador` | ✅ |
| C-19 | 3.1 | Problemas de qualidade encontrados e tratamento de cada um | E§2 "Problemas de qualidade"; `resultado.problema_qualidade`; Tela 3 `/dados` | ✅ |
| C-20 | 3.1 | EDA: uso no tempo, por modelo, idioma, tema, tamanho; padrões, concentrações, anomalias; só gráficos que levaram a conclusão | E§2; `docs/figuras/01..06` + `conclusoes.md` (uma frase por gráfico) | ✅ |
| C-21 | 3.1 | O que os dados permitem medir, o que não, e que dados faltam | E§2 "O que dá e o que não dá para medir"; E-resumo (efeito mínimo detectável ~5 p.p.) | ✅ |
| C-22 | 3.1 | Sugestões para o assistente (onde falha, temas/respostas que afastam) e para o dashboard (indicadores/telas pensados após ver os dados) | E§10 (assistente e dashboard) | ✅ |
| C-23 | 3.2 | Efeito de cada fator no retorno 7d com IC, ordenado por tamanho | E§3 (tabela); Tela 2 (ranking ordenado, um ponto por fator com a margem de erro); `/api/fatores/efeitos`; `resultado.efeito_fator` | ✅ |
| C-24 | 3.2 | Fatores de confusão e como tratou (comparar grupos semelhantes); o que prova e o que não prova | E§3 "Fatores de confusão" e "O que prova e o que não prova"; `docs/robustez_recusa.md`; `resultado.balanco_propensao` | ✅ |
| C-25 | 3.2 | Uma semana em que o retorno caiu/subiu e o que explica: mudança de perfil (mix) ou de taxa dentro do perfil | E§4 (20/11/2023 e 01/05/2023, mix × taxa); BDR-09; Tela 1 (cartão da semana: público × comportamento); `/api/semana/decomposicao` | ✅ |
| C-26 | 3.2 | Três achados para o cliente e a decisão que cada um sustenta | E-resumo (3 achados com decisão e limite); `seeds/achados.yaml` → `resultado.achado`; `/api/achados` | ✅ |
| C-27 | 3.3 | Telas: pergunta que cada uma responde, gráficos e por que esse tipo | E§5 (3 capturas; o título de cada tela é a pergunta; a legenda diz o gráfico e por quê) | ✅ |
| C-28 | 3.3 | Indicadores: definição, fórmula, denominador, período de referência, SQL de cada um; o que a tela mostra quando a base é pequena demais | `sql/transform/50_dicionario.sql` → `mart.dicionario_indicador` (com `sql_referencia`); `/api/dicionario`; Tela 3; E§5 regra de "pouca gente"; BDR-07 | ✅ |
| C-29 | 3.3 | Arquitetura: fluxo bruto→tela com diagrama; componentes AWS e stack front/back com porquê; modelo da base analítica; endpoints (nome, entrada, saída) | ARQ§1 (diagrama + `fluxo-bruto-tela.png`), ARQ§2–3 (AWS + `implantacao-aws.png`), **ARQ§5 modelo da base e ARQ§6 endpoints (acrescentados em 13/11)**; ADR-01, ADR-06 | ✅ |
| C-30 | 3.3 | Outros países: idioma da interface, fuso de cada país, comparação entre eles | ARQ§4 (país como parâmetro; idioma em `app/mensagens/pt.json`; `fuso_pais`; comparação por mix × taxa); E§6 | ✅ |
| C-31 | 3.3 | Performance: o que é pré-calculado, o que vai para cache, quando expira, como mede tempo de resposta | E§6; ADR-07 (pré-cálculo na carga, cache invalidado por lote); `docs/desempenho.md` (`Server-Timing`, 12 s → 0,33 s) | ✅ |
| C-32 | 4.1 | O que registrar em cada camada (carga, base analítica, backend, tela) para investigar número errado | E§7 "O que registramos em cada camada"; `ops.lote_carga`, `ops.rejeitado`, `ops.reconciliacao`; log JSON com `request_id` (`app/lib/api.ts`) | ✅ |
| C-33 | 4.1 | Como perceber divergência dashboard × base antes do cliente | E§7 "Como perceber a divergência" (reconciliação de 9 métricas a cada carga, 3 regras de alerta; construído e testado em 16/11: `loader/alerta.py`, `tests/test_alerta.py`, `--demo` sem credencial; sem canal de envio externo) | ✅ |
| C-34 | 4.1 | Testes automatizados que impedem a definição de indicador mudar sem ninguém perceber; caminho até produção (ambientes, migrações, deploy) | E§7 "Testes" e "Caminho até produção"; `tests/esperado.py`, `tests/`; `sql/migrations` + `sql/migrations_down` (16 + 16, inversas executadas em 16/11 com `scripts/reversao_banco.py`); `.github/workflows/ci.yml` (comandos rodados localmente em 16/11; esteira no GitHub não executada, repositório privado) | ✅ |
| C-35 | 4.2.1 | Incidente: por onde começaria e por quê | E§8 Pergunta 1 | ✅ |
| C-36 | 4.2.2 | Em qual camada está a falha + evidências + consulta para confirmar | E§8 Pergunta 2; `docs/incidente/confirmacao.sql`, `scripts/incidente_confirmacao.py`, `docs/incidente/evidencia.md` | ✅ |
| C-37 | 4.2.3 | Trecho de código que causa + correção escrita | E§8 Pergunta 3; `docs/incidente/correcao/carga_corrigida.py`, `route_corrigida.ts` | ✅ |
| C-38 | 4.2.4 | O que mais fazer além do código + como evitar recorrência | E§8 Pergunta 4; `tests/test_regressao_incidente.py` (T-503) | ✅ |
| C-39 | 4.2.5 | O que dizer à gerente de produto durante e depois | E§8 Pergunta 5 | ✅ |
| C-40 | 4.3 | Riscos principais + decisões a levar ao time/cliente antes de implementar (fora do seu escopo) | E§9 (6 riscos × decisão de quem) | ✅ |
| C-41 | 5 | Parágrafo final: ferramentas de IA e para quê; o que conferiu/corrigiu/descartou; horas aproximadas | E§11; `docs/conferi_da_ia.md`; `docs/horas.md` (~22 h) | ✅ |
| C-42 | 6 | 8 critérios de avaliação (Análise, Discovery/EDA, Investigação/sustentação, Dashboard, Construção/código, Clareza/premissas, Apresentação, Uso de IA) | Análise: C-05/06/23–26 · Discovery/EDA: C-08/19/20 · Sustentação: C-32–39 · Dashboard: C-07/27/28 · Código: C-14/15/34 · Clareza: C-13/16/21 · Apresentação: C-04 (M7) · IA: C-18/41 | ✅ (apresentação: depois do envio) |

## Resultado da conferência final (15/11/2026)
- **40 ✅ · 1 🔶 · 1 ⬜.** O 🔶 é o envio do e-mail (C-01). O ⬜ é a apresentação, depois do envio (C-04).
- Conferências feitas no fechamento: números de `docs/entrega.md` contra `resultado.*` e `mart.*`; subida do zero a partir do zip em pasta limpa; varredura de segredos e de conteúdo de conversa no zip; as 3 telas clicadas por inteiro (131 estados).
- Lacuna encontrada e corrigida em 13/11: faltavam o modelo da base e os endpoints com entrada e saída em `arquitetura.md` (C-29) e o idioma da interface e a comparação entre países (C-30).

## Revisão de 15/11/2026 (noite), depois de enxugar o documento
- `docs/entrega.md` reescrito a pedido do Vinícius (mais curto, 11 seções, PDF de 7 páginas com as cores do painel, 6 figuras da EDA e 3 capturas). O mapa item a item foi para `docs/mapa_enunciado.md`.
- Reconferidas as 42 linhas contra o texto novo. O corte tinha enfraquecido C-16 (primeira experiência), C-27, C-30, C-31, C-32, C-34 (caminho até produção) e C-38 (teste de regressão); todos repostos em versão curta.
- "O que faria diferente" (C-04) saiu do PDF: o enunciado pede na apresentação.
