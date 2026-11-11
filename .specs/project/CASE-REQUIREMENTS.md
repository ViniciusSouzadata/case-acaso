# Requisitos do case — rastreabilidade (fonte: PDF "Desafio Técnico Acaso", 10/11/2026)

> Cada linha é uma exigência literal do PDF. Todo REQ-nnn das features aponta para um C-nn.
> A auditoria final (fase A do BSPA) só fecha quando todas as linhas tiverem evidência.

| ID | § | Exigência (literal ou quase) | Evidência na entrega | Status |
|----|---|------------------------------|----------------------|--------|
| C-01 | Como funciona | Entrega até seg 16/11 23h59 para nathalia.anjos@aca.so e daniele.cardoso@aca.so | E-mail enviado (meta: seg à tarde) | ⬜ |
| C-02 | Como funciona | Priorizar decisões claras e justificadas, não documento longo; ~12h esperadas | Doc curto + ADR/BDR | ⬜ |
| C-03 | Escopo | Análise executada + dashboard funcionando (frontend, backend, base analítica) + doc curto com achados e decisões | | ⬜ |
| C-04 | Apresentação | 20 min apresentação + 40 min técnica: fluxo de construção, decisões registradas, o que faria diferente | M7 prep | ⬜ |
| C-05 | 1 | Pergunta: o que faz voltar em até 7 dias; quais fatores, quanto pesa cada um, quanto é causa × seleção | | ⬜ |
| C-06 | 1 | Análise estatística, não só descritiva: efeito com incerteza, separando efeito do assistente do perfil | | ⬜ |
| C-07 | 1 | Usuário final não técnico; resultados por dashboard (não notebook); cada tela se explica sozinha; cada número com definição e fonte; cada efeito com incerteza | | ⬜ |
| C-08 | 2 | WildChat-1M, só country = 'Brazil' | | ⬜ |
| C-09 | 2.1 | Não há ID de usuário: como decidir que duas conversas são da mesma pessoa (avaliado) | | ⬜ |
| C-10 | 2.2 | Dashboard não lê base bruta; base analítica desenhada e populada por você | | ⬜ |
| C-11 | 2.2 | Toda infra e custo do dashboard na AWS, inclusive LLM; análise com qualquer ferramenta; entrega local + descrever implantação | | ⬜ |
| C-12 | 2.2 | Dados pessoais: dizer o que o dashboard mostra e o que nunca mostra | | ⬜ |
| C-13 | 2.3 | Premissas (uso, sessão, fuso, período...): registrar cada uma e o que mudaria se estiver errada | | ⬜ |
| C-14 | 3 | Sobe do zero com um comando (ex. docker compose up), carrega base analítica a partir da bruta, ≥2 telas com dados reais | | ⬜ |
| C-15 | 3 | Repositório com instruções + ADRs e BDRs (contexto, opções consideradas, escolha) | | ⬜ |
| C-16 | 3.1 | Definição de usuário, sessão, primeira experiência, retorno + quanto o resultado muda se a definição mudar | | ⬜ |
| C-17 | 3.1 | Variáveis da 1ª experiência (modelo, tema, tamanho e qualidade da resposta, recusas, turnos, horário, idioma) e derivação de cada uma | | ⬜ |
| C-18 | 3.1 | Se usar IA para classificar, como conferiu o resultado | | ⬜ |
| C-19 | 3.1 | Problemas de qualidade encontrados e tratamento de cada um | | ⬜ |
| C-20 | 3.1 | EDA: uso no tempo, por modelo, idioma, tema, tamanho; padrões, concentrações, anomalias; só gráficos que levaram a conclusão | | ⬜ |
| C-21 | 3.1 | O que os dados permitem medir, o que não, e que dados faltam | | ⬜ |
| C-22 | 3.1 | Sugestões para o assistente (onde falha, temas/respostas que afastam) e para o dashboard (indicadores/telas pensados após ver os dados) | | ⬜ |
| C-23 | 3.2 | Efeito de cada fator no retorno 7d com IC, ordenado por tamanho | | ⬜ |
| C-24 | 3.2 | Fatores de confusão e como tratou (comparar grupos semelhantes); o que prova e o que não prova | | ⬜ |
| C-25 | 3.2 | Uma semana em que o retorno caiu/subiu e o que explica: mudança de perfil (mix) ou de taxa dentro do perfil | | ⬜ |
| C-26 | 3.2 | Três achados para o cliente e a decisão que cada um sustenta | | ⬜ |
| C-27 | 3.3 | Telas: pergunta que cada uma responde, gráficos e por que esse tipo | | ⬜ |
| C-28 | 3.3 | Indicadores: definição, fórmula, denominador, período de referência, SQL de cada um; o que a tela mostra quando a base é pequena demais | | ⬜ |
| C-29 | 3.3 | Arquitetura: fluxo bruto→tela com diagrama; componentes AWS e stack front/back com porquê; modelo da base analítica; endpoints (nome, entrada, saída) | | ⬜ |
| C-30 | 3.3 | Outros países: idioma da interface, fuso de cada país, comparação entre eles | | ⬜ |
| C-31 | 3.3 | Performance: o que é pré-calculado, o que vai para cache, quando expira, como mede tempo de resposta | | ⬜ |
| C-32 | 4.1 | O que registrar em cada camada (carga, base analítica, backend, tela) para investigar número errado | | ⬜ |
| C-33 | 4.1 | Como perceber divergência dashboard × base antes do cliente | | ⬜ |
| C-34 | 4.1 | Testes automatizados que impedem a definição de indicador mudar sem ninguém perceber; caminho até produção (ambientes, migrações, deploy) | | ⬜ |
| C-35 | 4.2.1 | Incidente: por onde começaria e por quê | | ⬜ |
| C-36 | 4.2.2 | Em qual camada está a falha + evidências + consulta para confirmar | | ⬜ |
| C-37 | 4.2.3 | Trecho de código que causa + correção escrita | | ⬜ |
| C-38 | 4.2.4 | O que mais fazer além do código + como evitar recorrência | | ⬜ |
| C-39 | 4.2.5 | O que dizer à gerente de produto durante e depois | | ⬜ |
| C-40 | 4.3 | Riscos principais + decisões a levar ao time/cliente antes de implementar (fora do seu escopo) | | ⬜ |
| C-41 | 5 | Parágrafo final: ferramentas de IA e para quê; o que conferiu/corrigiu/descartou; horas aproximadas | | ⬜ |
| C-42 | 6 | 8 critérios de avaliação (Análise, Discovery/EDA, Investigação/sustentação, Dashboard, Construção/código, Clareza/premissas, Apresentação, Uso de IA) | Auditoria cruzada | ⬜ |
