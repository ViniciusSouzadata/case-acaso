<!-- RASCUNHO da Sessão A (T-604), em revisão pelo planejador e pelo Vinícius. Marcas "[EM REVISÃO]" = o número ou a frase pode mudar:
     (a) preços da AWS "a conferir"; (b) total de horas atualizado no envio.
     Cada seção cita o C-nn do enunciado que responde. Números vêm de resultado.*, mart.* e do STATE; nada sobre clientes da Acaso. -->

# Retenção de um assistente de IA: o que faz a pessoa voltar em 7 dias

## 1. Resumo  (C-02, C-05, C-26)

De cada 100 pessoas que experimentam o assistente pela primeira vez, **24 voltam em até 7 dias** (23,86%; intervalo de 95%: 22,19% a 25,62%; 2.372 usuários, 566 voltaram). Se "voltar" exigir outro dia, a taxa é de 17% (16,86%): a manchete honesta é **"entre 17% e 24%, conforme o que o cliente chama de voltar"**. Base: WildChat, conversas do Brasil de abr/2023 a abr/2024.

Três achados (texto completo em `seeds/achados.yaml` e na tabela `resultado.achado`):
1. **A recusa na primeira resposta é o único comportamento do assistente ligado a menos retorno.** Entre 2.372 novos usuários, 132 receberam uma recusa na primeira resposta: voltaram 13 de 132 (9,8%), contra 553 de 2.240 (24,7%) dos demais. Comparando pessoas de perfil parecido, são 16,4 pontos a menos (de 11,5 a 21,4); com "voltar em outro dia", 9 de 132 (6,8%) contra 391 de 2.240 (17,5%), 11,5 pontos a menos (de 7,3 a 15,7). O grupo é pequeno. Antes de olhar esse efeito, a marcação de recusa foi trocada de palavras-chave por IA porque a validação manual de 200 conversas mostrou que as regras erravam (com elas a diferença parecia 3,3 pontos, de −10,1 a +3,5). *Decisão:* tratar a taxa de recusa como indicador de saúde do assistente e testar, de forma controlada, uma recusa que ofereça alternativa útil. *Limite:* é comparação, não experimento, e o conjunto de dados não traz as conversas tóxicas, onde as recusas são mais comuns.
2. **Trocar de modelo ou mudar o formato da resposta não mostrou ganho de retorno.** GPT-4 contra GPT-3.5: −2,9 pontos (de −8,0 a +2,2); os dados descartam um ganho acima de cerca de 2 pontos. *Decisão:* não justificar um modelo mais caro por retenção; se a troca vier por qualidade, medir com teste controlado.
3. **Quedas semanais isoladas enganam: a maior era efeito do início da coleta.** A semana de 01/05/2023 parecia cair 17,1 pontos (p = 0,013); com o início da coleta tratado com folga, cai 7,7 (p = 0,13). A semana de 20/11/2023 (novo modelo) caiu 4,9, dentro da variação normal (p = 0,43). Nas 33 semanas testadas, só 1 passou do limite, perto do que o acaso produz. *Decisão:* o alerta do painel só dispara acima da variação normal e ignora o início da coleta.

Sinais descritivos (não são achados): quem tem 4 ou mais mensagens na primeira sessão volta mais (32,9% contra 17,2% com 1), e o tema da conversa (IA de concordância moderada) mostra, por exemplo, conversa pessoal com retorno menor; os dois acontecem junto do interesse da pessoa e não provam causa.

O que **os dados não permitem**: separar causa de seleção (é observacional), enxergar efeito menor que cerca de 5 pontos (4,9 com grupos iguais), nem reconhecer a mesma pessoa que troca de rede ou de aparelho.

## 2. Definições e premissas  (C-09, C-13, C-16)

Cada linha: o que escolhi e o que muda se estiver errado (taxa recalculada com a mesma função; oficial 23,86%). Detalhe em `docs/decisoes/`.

| Premissa | Escolha | Se estiver errada | Registro |
|---|---|---|---|
| Quem é um usuário | IP + família do navegador (sem versão) | só IP: 23,94%; IP + user-agent completo: 25,14% (e +21% de usuários) | BDR-01 |
| O que é sessão | intervalo ≤ 30 min entre o fim de uma conversa e o início da próxima | 60 min: 21,54% | BDR-02 |
| O que é "voltar" | nova sessão com início em até 7 dias (168 h) do início da 1ª | "só em outro dia": 16,86% (cerca de 166 dos 566 retornos são outra sessão no mesmo dia) | BDR-02 |
| O que conta como uso | ao menos 1 pergunta não vazia e 1 resposta; 141 perguntas vazias e 76 conversas fora | contando as vazias: 23,69% | BDR-03 |
| Burn-in e coortes imaturas | 14 dias iniciais e quem não tem 7 dias completos ficam fora (64 e 51 usuários) | sem burn-in: 24,01%; com burn-in de 28 dias: 23,70% (2.232 usuários) | BDR-04 |
| Tráfego anômalo | IP com 200+ conversas ou 10+ user-agents fica fora (11 usuários, 7 IPs) | com eles: 24,08% | BDR-05 |
| Fuso | America/Sao_Paulo | UTC: mesma taxa; 44 usuários mudam de semana | BDR-06 |
| Amostra mínima | toda taxa com intervalo e n; abaixo do mínimo, "amostra insuficiente" | — | BDR-07 |

## 3. O que os dados mostram  (C-17, C-18, C-19, C-20, C-21)

Só os gráficos que levaram a uma conclusão (`docs/figuras/`, frases em `conclusoes.md`):
- **Volume:** mediana de 163 conversas por semana (de 40 a 616). 4 semanas com queda forte (10/04/2023, 09/10/2023, 29/01/2024, 05/02/2024).
- **Concentração:** 2.385 IPs; o 1% mais ativo (24 IPs) responde por 41% das conversas; o mais ativo sozinho, por 13,4% (1.557 conversas). Por isso o tráfego anômalo fica fora (BDR-05).
- **Retorno por semana:** a faixa de incerteza de cada ponto tem em média 22 pontos de largura; boa parte da variação semanal é ruído.
- **Turnos:** 56% das conversas têm um único turno e 84% têm até três. O engajamento vem depois da resposta, então vira sinal de engajamento, não fator do assistente (BDR-08).
- **Idioma:** 70% das conversas em português. O idioma "divergente" aparece em 61% das perguntas de até 30 caracteres contra 10% nas mais longas: em pergunta curta é erro de detecção, então o fator só vale para perguntas com mais de 30 caracteres.
- **Tema** (IA com concordância moderada, descritivo): o retorno vai de 32% (trabalho/negócios e escrita/tradução) a 17% (conversa pessoal/conselho); só a conversa pessoal se distingue dos demais temas (−9,2 pontos, de −12,8 a −5,2, diferença simples).

**Variáveis da primeira experiência** (C-17): modelo (família), tema, tamanho da pergunta e da resposta, recusa, idioma, idioma divergente, dispositivo, período do dia, fim de semana, região, era do modelo, e (como engajamento) turnos e conversas na 1ª sessão. Cada uma é derivada na carga, com o código em `loader/derivar.py` e o dicionário na tela "Posso confiar nestes números?".

**Como conferi a IA que classifica** (C-18): 200 conversas rotuladas por mim, sem ver o que a máquina respondeu. Com palavras-chave (`regras`): tema com 36,5% de acerto (kappa 0,27) e recusa com 81,0% (kappa 0,37); na população, a revocação da recusa é de 48,8% (pega metade das recusas reais) e só 30,2% do que marca como recusa é recusa. Com o LLM (Claude Haiku 5.5, pela OpenRouter; o Bedrock da minha conta devolveu `ValidationException: Operation not allowed` e não rodou), nas mesmas 200: tema com 56,0% de acerto (kappa 0,48) e recusa com 92,0% (kappa 0,59; precisão ponderada 81%, revocação ponderada 86%). **Tema continua descritivo** (kappa moderado); a recusa ficou bem mais confiável, e isso **muda o efeito da recusa** (seção 4). Um segundo modelo (Nova Lite) foi descartado: 40% dos itens sem resposta válida. Números e custo: ADR-09, `docs/validacao_llm.md`.

**Problemas de qualidade e tratamento** (C-19): 141 perguntas vazias (não contam como uso), 76 conversas sem uso, 93 conversas com texto repetido, 175 IPs que mudam, 56 conversas com dado removido pelos autores, 0 marcadas como tóxicas (removidas na origem), idioma divergente em pergunta curta (restrito). Tela "Posso confiar nestes números?" lista cada um com o tratamento.

**O que dá e o que não dá para medir; que dados faltam** (C-21): dá para medir associação entre a primeira experiência e o retorno. Não dá para provar causa, identificar a mesma pessoa em redes ou aparelhos diferentes, nem saber o que mudou no produto em cada semana. Faltam: ID de login, versão do produto por data, satisfação declarada e o motivo de a pessoa ter parado.

## 4. Efeitos  (C-05, C-06, C-23, C-24)

Efeito = diferença na taxa de retorno em pontos percentuais, com intervalo de 95%. "Ajustado" compara pessoas parecidas nos outros fatores (regressão logística com erro agrupado por IP). **Dos 25 efeitos ajustados, só um passa a correção para muitos testes (Benjamini-Hochberg, 5%): a recusa na primeira resposta.**

| Fator (contra a referência) | Bruto | Ajustado (IC 95%) | Leitura |
|---|---:|---|---|
| **Recusa na 1ª resposta** (132 usuários) | −14,8 | **−16,4 (−21,4 a −11,5)** | passa a correção; 13 de 132 voltaram contra 553 de 2.240; fator escondido precisaria ser muito forte (E-value 5,3); segundo método: grupo não comparável |
| Modelo GPT-4 (contra GPT-3.5) | +0,1 | −2,9 (−8,0 a +2,2) | não se distingue de zero; pelo 2º método (comparação ponderada): −6,1 (−12,7 a +0,4) |
| Idioma divergente (pergunta > 30 caracteres) | +3,0 | +0,1 (−7,7 a +7,9) | não se distingue de zero; 158 usuários |
| Resposta de 301 a 1.000 caracteres (contra até 300) | +8,8 | +4,7 (−1,5 a +10,8) | o bruto engana: boa parte era perfil e era do modelo |
| Resposta com mais de 2.500 caracteres | +7,9 | +0,5 (−6,0 a +7,0) | idem |
| Tema: conversa pessoal (contra demais temas) | −10,0 | −8,2 (−14,3 a −2,1) | não passa a correção; tema é descritivo (IA de concordância moderada) |
| Engajamento: 4+ turnos na 1ª sessão (descrição) | +15,6 (11,3 a 19,9) | fora do modelo | sinal, não causa (BDR-08) |

**Robustez da recusa** (`docs/robustez_recusa.md`): o efeito ajustado é −16,4 na definição oficial, −16,4 (só IP), −14,4 (IP + navegador completo), −15,4 (sessão de 60 min) e −16,3 (burn-in de 28 dias); as 132 recusas estão em 131 IPs (o maior tem 2), e sem os 10 IPs com mais recusas o efeito é −16,4; a direção se repete nos temas com recusas suficientes; com "voltou em outro dia" o ajustado é −11,5 (−15,7 a −7,3). Erro de marcação que não depende de quem volta tende a diminuir a diferença; uma correção simples leva o bruto de −14,8 para cerca de −18,5. Com a recusa marcada por regras, nos mesmos usuários, o ajustado era −3,3 (−10,1 a +3,5): as regras marcavam 63 usuários que a IA não considera recusa e perdiam 42.

**Fatores de confusão e como tratei** (C-24): perfil e era do modelo entram como controle; para modelo, recusa, idioma divergente e a "virada" de dez/2023 comparei pessoas de perfil parecido (ponderação por propensão, balanço conferido e erro por bootstrap agrupado por IP). A virada de dez/2023, quando o GPT-4 virou o padrão, não mostra mudança: +2,0 (−2,1 a +6,1). Para recusa e idioma divergente **não deu para montar um grupo de comparação equilibrado** (cerca de 130 a 160 usuários em cada grupo): o resultado fica no modelo ajustado. É limite do dado, não do método. A leitura é a mesma nas 4 definições de usuário e sessão.

**O que prova e o que não prova:** mostra que a recusa na primeira resposta anda junto de bem menos retorno, e que modelo, tamanho da resposta e idioma não mostram efeito distinguível de zero (um ganho de modelo acima de cerca de 2 pontos é incompatível com os dados). Não prova causa: a recusa pode ser sinal de um pedido que o produto não atende, e só vemos parte das recusas (as conversas tóxicas foram removidas na origem). Para afirmar causa, teste controlado (BDR-08, ADR-10).

## 5. A semana de 20/11/2023 e a de 01/05/2023  (C-25)

Cada semana foi comparada a 4 semanas de coorte **limpas** (que começam pelo menos 28 dias depois do primeiro dado), com decomposição em **mudança de público (mix)** e **mudança de taxa dentro do público**.

| Semana | Retorno | Base | Diferença | Mix / taxa | p |
|---|---|---|---:|---|---:|
| **20/11/2023** (a do case) | 21,5% (n=65) | 26,4% (n=197), 4 semanas anteriores | −4,9 pontos | −0,4 / −4,4 | 0,43 |
| 01/05/2023 | 16,7% (n=84) | 24,4% (n=340), 4 semanas **seguintes** | −7,7 | −0,6 / −7,1 | 0,13 |
| 17/07/2023 (só na tabela) | 9,1% (n=33) | 22,5% (n=178), 4 semanas anteriores | −13,4 | −0,5 / −12,9 | 0,08 |

- **20/11/2023 está dentro do ruído:** quase toda a diferença é de taxa, e o método não confirma queda.
- **01/05/2023 era um artefato do início da coleta.** Na primeira leitura (base = as 2 semanas anteriores, 33,8%) era a maior queda da série (−17,1 pontos, p = 0,013). Com burn-in de 28 dias as duas semanas de base caem fora e, contra as semanas seguintes, a queda vira −7,7 pontos (p = 0,13).
- Em todas as semanas com amostra suficiente e base limpa (33), só 1 teve p < 0,05; o acaso sozinho produz cerca de 2. **Queda semanal isolada não sustenta conclusão.** Regra adotada: semana de base começa pelo menos 28 dias depois do primeiro dado (BDR-09).

## 6. Dashboard  (C-07, C-12, C-27, C-28)

Três telas, cada uma com uma pergunta, em português simples; cada número tem definição, fonte e intervalo.

| Tela | Pergunta | Gráfico e por quê |
|---|---|---|
| **Retenção** | "De cada 100 pessoas que experimentam o assistente, quantas voltam em até 7 dias? E isso está mudando?" | linha por semana com faixa de incerteza (mostra tendência sem enganar com ponto solto); pontos de sensibilidade (a taxa muda pouco com a definição); cascata para a semana (separa público de taxa) |
| **Fatores** | "Quais fatores da primeira experiência mais pesam para a pessoa voltar, e quanto disso é efeito do assistente?" | "floresta" (um ponto por fator com o intervalo; o que cruza o zero é visível de relance), em 3 grupos: assistente, perfil, engajamento |
| **Posso confiar nestes números?** | idem | carga, reconciliação, problemas de qualidade, validação do classificador e dicionário de indicadores, em tabelas |

**Regra de amostra pequena:** abaixo do n mínimo o painel mostra "amostra insuficiente" no lugar do número; coortes sem 7 dias completos aparecem marcadas. **O que mostra:** só agregados. **Nunca mostra:** texto de conversa, IP, user-agent (BDR-10). Ficha dos indicadores (definição, fórmula, denominador, período e SQL): `mart.dicionario_indicador` e tela de dados.

## 7. Arquitetura, implantação e custo  (C-11, C-29, C-30, C-31)

- **Fluxo:** arquivo bruto → carga (papel `loader_rw`) → `stg` (restrito) → `mart` e `resultado` → API (papel `app_ro`, só leitura) → telas. Diagrama e modelo da base em `docs/arquitetura/arquitetura.md`.
- **Pré-cálculo e cache:** os indicadores são pré-agregados na carga; a API guarda em cache e invalida quando muda o lote (ADR-07). Tempos medidos em `docs/desempenho.md`.
- **AWS (desenho, não implantado):** RDS PostgreSQL, containers para app e carga, balanceador, S3 para o bruto, Secrets Manager, CloudWatch e **Bedrock** para o LLM (ADR-08, ADR-09). **Custo mensal estimado: cerca de US$ 43 [a conferir no AWS Pricing Calculator]**, mais o LLM, medido: **US$ 0,24 para classificar 2.657 conversas (≈US$ 0,08 por 1.000; a base Brasil inteira ≈US$ 0,94; o WildChat inteiro ≈US$ 68)**, `docs/custo_llm.md`.
- **Outros países:** o país é parâmetro (uma carga por país no mesmo banco), com idioma da interface, fuso por país e comparação padronizada pelo mix; amostras pequenas aparecem como "amostra pequena" (seção 4 de `arquitetura.md`).

## 8. Sustentação: como eu saberia que um número está errado  (C-32, C-33, C-34)

### O que registramos em cada camada
| Camada | O que fica registrado | Para que serve |
|---|---|---|
| **Carga** | um registro por execução em `ops.lote_carga` (arquivo de origem, checksum, versão da definição, linhas lidas, gravadas e rejeitadas, início, fim, status); cada linha rejeitada em `ops.rejeitado` com o motivo | saber de qual arquivo e de qual versão da regra veio o número, e se a carga foi parcial |
| **Base analítica** | versão da definição em `ops.parametros` e em `resultado.meta`; reconciliação bruto × base em `ops.reconciliacao` (9 métricas) | dizer "o número mudou porque a regra mudou" ou "porque o dado mudou" |
| **Backend** | um log em JSON por requisição, com `request_id`, rota, tempo (`Server-Timing`) e a versão dos dados; erro devolve o `request_id` | achar a consulta exata que gerou o que a tela mostrou |
| **Tela** | `request_id` visível no erro; rodapé com data da carga e versão da definição | o usuário consegue citar o que viu |

**Caminho para investigar um número errado:** tela (`request_id` e rodapé) → log da requisição → consulta SQL → tabela `mart` → lote em `ops.lote_carga` → arquivo bruto. Em nenhum ponto aparece texto de conversa, IP ou user-agent.

### Como perceber a divergência antes do cliente
- **Reconciliação automática a cada carga:** o loader refaz 9 métricas direto do arquivo bruto (conversas, IPs, usuários, elegíveis, retornos, semanas maduras e semanas divergentes) e compara com a base. Hoje: diferença 0 nas 9.
- **Regras de alerta** (descritas; a reconciliação já roda, o envio do alerta fica como próximo passo):
  1. diferença acima da tolerância em qualquer métrica reconciliada;
  2. "novos usuários" da semana mais de 3 desvios-padrão fora da média das 8 semanas anteriores;
  3. salto no número de user-agents por IP (o sinal exato do incidente).

### Testes que impedem a definição de mudar em silêncio
- **Base sintética de resposta conhecida:** casos escritos à mão (retorno em 6 d 23 h conta, 7 d + 1 min não; intervalo de exatamente 30 min é a mesma sessão; troca de versão do navegador é a mesma pessoa; 1 IP com 12 user-agents é tráfego anômalo; conversa vazia não conta). A resposta esperada fica em `tests/esperado.py`.
- **Versão da definição:** os parâmetros do banco são comparados com um arquivo de referência; mudar um sem subir a versão derruba o teste.
- **Contrato da API:** campo a mais, a menos ou de tipo errado falha.
- **Um comando:** `make test` (ou `docker compose run --rm loader ...`). Provei que os testes pegam: gap de sessão de 30 para 60 minutos sem subir a versão derrubou o teste de versão; trocar `<=` por `<` na janela de 7 dias só foi pego depois que acrescentei os testes de borda.

### Caminho até produção
1. **Ambientes:** local (compose) → homologação → produção, com a mesma imagem e configuração por variável.
2. **Migrações:** arquivos SQL numerados e aplicados em ordem, com registro em `ops.schema_migrations`. Cada migração tem o passo inverso escrito em `sql/migrations_down/` (rodado à mão, em transação, de trás para frente; **escrito e verificado na estrutura, não executado contra um banco ainda**).
3. **Deploy:** imagem versionada (a tag é o commit); nunca construir em produção.
4. **Verificação depois do deploy:** `/api/saude` e uma reconciliação; só depois o tráfego entra.
5. **Reversão:** voltar para a imagem anterior; se a migração mudou dados, restaurar pelo backup ou pelo passo inverso (`sql/migrations_down/`). Reconstruir os marts a partir do bruto é seguro porque a carga é idempotente.
6. **CI:** `.github/workflows/ci.yml` roda lint (ruff, só erros de sintaxe e nomes não definidos), a suíte Python contra um Postgres do compose, e `tsc` + `vitest` do app antes de aceitar a mudança. **Configurado, não executado aqui** (o repositório privado ainda não roda o workflow; sintaxe revisada à mão e o lint passa na minha máquina).

## 9. Incidente: a retenção do dashboard caiu de 31% para 18%  (C-35 a C-39)

### Pergunta 1 — Por onde eu começaria e por quê
Reconciliando as duas fontes **na mesma granularidade** (semana). A tabela do enunciado já aponta o caminho:

| Semana | Novos (dashboard) | Novos (relatório) | Voltaram (dashboard) | Voltaram (relatório) |
|---|---:|---:|---:|---:|
| 06/11 | 1.210 | 1.150 | 375 | 345 |
| 13/11 | 1.188 | 1.131 | 368 | 351 |
| 20/11 | **2.034** | 1.172 | 366 | 352 |

Quem **voltou** fica estável nas duas fontes; quem **chegou** explode só no dashboard (+862, +73,5%). A queda não é de comportamento: é de **contagem de usuários novos**. Em semanas normais as duas fontes já divergiam cerca de 5%, o que indica definições de usuário diferentes desde antes. Com cerca de 1.200 usuários por semana, o intervalo de 95% da taxa é de aproximadamente ±2,6 pontos: 31% para 30% é ruído; 31% para 18% não é.

### Pergunta 2 — Em qual camada está a falha, com que evidência
Na **carga**, na definição de `usuario_id`. O relatório conta por `hashed_ip`; a carga conta por `hashed_ip|user-agent`. O endpoint calcula certo sobre o que recebe, e a tela só exibe.

Há três explicações possíveis para "mais novos, mesmos retornos", e todas apontam para a mesma linha: um IP com user-agent rotativo (robô), um IP compartilhado com muita gente de verdade, ou usuários antigos que atualizaram o navegador. A carga duplicada fica descartada: `ON CONFLICT DO NOTHING` não duplica a conversa, e duplicar conversa não cria usuário.

**Consulta de confirmação** (`docs/incidente/confirmacao.sql`; a mesma lógica roda no arquivo bruto com `scripts/incidente_confirmacao.py`): para cada semana, usuários novos pela chave IP + user-agent, pela chave IP, quantos "novos" caem em IP que já existia e o máximo de user-agents novos por IP.

**Mecanismo mostrado com dado real** (WildChat Brasil, `docs/incidente/evidencia.md`): 2.385 usuários pela chave IP contra **2.895 pela chave IP + user-agent (+21,4%)**, 510 "novos" a mais caindo em IP já visto, e até 35 user-agents diferentes em um único IP. Os números do enunciado (1.210 por semana) não existem neste dado; o que mostro é o mecanismo.

### Pergunta 3 — O trecho que causa o problema e a correção
O trecho: `chave = f"{hashed_ip}|{user-agent}"`. Cada versão de navegador, e cada navegador de um mesmo IP, vira "uma pessoa nova".

Outros defeitos do mesmo endpoint, mesmo sem relação direta com a queda: a "primeira vez" usa o **último** turno da conversa; coortes dos últimos 7 dias não são marcadas como imaturas; `date_trunc('week')` roda no fuso do banco (UTC); `ON CONFLICT DO NOTHING` congela conversa que continua em outro dia; a inserção é linha a linha, sem transação nem registro de lote.

**Correção escrita** em `docs/incidente/correcao/`:
- `carga_corrigida.py`: identidade vinda de **uma regra única** (IP + família do navegador, sem versão), upsert com `ON CONFLICT DO UPDATE`, **um lote em uma transação** e registro do lote.
- `route_corrigida.ts`: usuário vindo de `mart.dim_usuario`, início da primeira sessão (não o último turno), semana no fuso do país, coortes imaturas marcadas.
Os dois arquivos têm um comentário `DEFEITO:` em cada linha corrigida, e passam em `py_compile` e `tsc --noEmit --strict`.

### Pergunta 4 — O que mais fazer além do código e como evitar que volte
1. **Reprocessar o histórico** com a regra corrigida (a carga é idempotente) e **versionar** a mudança de definição.
2. **Alinhar a definição** com o relatório do time de dados: a causa organizacional são duas definições de usuário e nenhuma reconciliação.
3. **Reconciliação automática e alerta** (seção 4.1): salto de "novos" e de user-agents por IP.
4. **Teste de regressão** (`tests/test_regressao_incidente.py`): na base sintética, a troca de versão do navegador não cria usuário novo e o IP com 12 user-agents não entra nos "novos"; o teste também mostra que, com a chave do incidente, a mesma verificação falha.
5. **Registro pós-incidente:** causa, impacto, correção e o que mudou no processo; as semanas anteriores tinham cerca de 5% de viés que também foi corrigido.

### Pergunta 5 — O que eu diria à gerente de produto

**Durante (hoje):**
> "A queda de 31% para 18% é quase certamente de **medição**, não de comportamento: o número de pessoas que voltaram não mudou, só o de pessoas que chegaram. Por favor, **não tome decisão em cima do 18%**. Estou confirmando a causa e volto a falar com você até [horário]."

**Depois:**
> "A causa foi a forma como o dashboard identifica uma pessoa nova: uma troca de navegador estava contando como usuário novo. Com a regra corrigida, a retenção da semana de 20/11 é [X%], com margem de [±Y pontos]. As semanas anteriores tinham um erro pequeno (cerca de 5%), que também foi corrigido. A contagem agora é conferida automaticamente com o relatório do time de dados, e há um teste que impede esse erro de voltar. Os números que você já mostrou para outras pessoas: [lista], com a versão corrigida."

<!-- Os campos [horário], [X%] e [Y pontos] dependem de rodar a regra corrigida nos dados reais do cliente; no case não existem. -->

## 10. Riscos e decisões a levar ao time e ao cliente antes de implementar  (C-40)

| Risco | Decisão que não é minha |
|---|---|
| Não há ID de usuário: a identidade por IP + navegador erra nos dois sentidos | **Qual é a definição oficial de usuário?** O ideal é um ID de login; até lá, IP + família do navegador, com a sensibilidade sempre visível |
| O dado tem texto de conversa e IP (mesmo anonimizado) | **Política de retenção e base legal (LGPD):** por quanto tempo guardar, quem acessa, o que pode ir para um LLM. Com dado de cliente, só LLM dentro da conta (Bedrock) |
| Custo do LLM cresce com a base | **Orçamento de LLM** e quem aprova; o custo medido é ≈US$ 0,08 por 1.000 conversas (`docs/custo_llm.md`) |
| Mudar a definição de "voltar" muda o número oficial | **Quem aprova a mudança de definição** e como se comunica (a versão da definição fica no rodapé de toda tela) |
| A base é pequena (cerca de 2.400 usuários elegíveis): só se enxerga efeito grande | **O que é efeito que vale agir** e se vale um teste controlado no produto |
| Carga atualizada em lote | **SLA de atualização** (diária?) e o que o painel mostra quando a carga atrasa |

## 11. Sugestões  (C-22)

**Para o assistente** (com a cautela de que os dados não provam causa):
- **Recusa:** acontece em cerca de 6% das primeiras respostas e é o único comportamento do assistente ligado a menos retorno (16,4 pontos a menos, de 11,5 a 21,4). Acompanhar a taxa de recusa como indicador de saúde, revisar as recusas desnecessárias e testar de forma controlada uma recusa que ofereça alternativa útil. Os dados não provam que a recusa cause a saída.
- **Modelo:** não justificar a troca para um modelo mais caro por retenção (−2,9 pontos, de −8,0 a +2,2; ganho acima de cerca de 2 pontos é incompatível com os dados).
- **Resposta muito curta (até 300 caracteres):** retorno mais baixo no bruto; no ajuste o efeito encolhe e o intervalo cruza zero: não é onde priorizar.
- **Tema** (descritivo): conversa pessoal volta menos (−9,2 pontos na diferença simples); usar para entender o público, não para mudar o assistente.

**Para o dashboard** (indicadores pensados depois de ver os dados):
- Mostrar sempre o intervalo e o n ao lado de cada taxa e de cada efeito, com o aviso "não se distingue de zero".
- Mostrar "voltou em outro dia" ao lado da taxa oficial (17% × 24%).
- Sinalizar uma semana só quando a diferença passar da variação normal, ignorando as semanas do início da coleta, e dizer quantas semanas passariam por acaso.
- Mostrar a **taxa de recusa** na primeira resposta ao lado da retenção.
- Indicador de **tamanho da primeira sessão** como sinal de engajamento.
- Painel de reconciliação (bruto × base) visível ao cliente, para o número ser conferível.

## 12. O que eu faria diferente  (C-04, C-15)

- Com ID de login, trocaria a identidade por IP pela do usuário real e refaria toda a análise (o código recalcula tudo com um comando).
- Pediria dado de versão do produto por data, para explicar semanas como a de 01/05 em vez de só descrevê-las.
- Faria um teste controlado de recusa e de modelo: é a única forma de provar causa.
- Passaria os testes de definição para dbt se o time de dados já o usar (hoje: SQL versionado + pytest, ADR-03).
- Implantaria de fato na AWS; neste case é um desenho, com custo estimado (ADR-08).
- Carga incremental por lote, mantendo a mesma reconciliação (ADR-01).

## 13. Uso de IA  (C-41)

Usei assistentes de IA (Claude, pelo Claude Code) em duas funções: **planejamento** (especificações, desenho das decisões e revisão) e **execução** (código e testes, uma tarefa por vez), mais um LLM para classificar tema e recusa (a rodada foi pela OpenRouter; o Bedrock, o principal planejado, ficou bloqueado na minha conta). **Conferi** com testes e com os meus rótulos: 200 conversas rotuladas por mim contra a máquina (ADR-09), uma base sintética de resposta conhecida e reconciliação do bruto com a base (9 métricas, diferença 0). **Corrigi ou descartei**: o efeito marginal gerado na 1ª versão estimava +7,0 pontos onde o verdadeiro era +10,1 numa simulação (o teste pegou, corrigido); o "idioma divergente" bruto era ruído de detecção em pergunta curta (restrito); um teste de borda foi acrescentado porque trocar `<=` por `<` passava despercebido; a consulta de retenção levava 12 s por chamada e passou a 0,33 s depois de achar uma subconsulta repetida. Mais casos em `docs/conferi_da_ia.md`. **Horas aproximadas:** cerca de 14 h até a manhã de 12/11 (ter ~6 h, qua ~6 h, qui ~2 h; estimativa minha, em `docs/horas.md`); total final atualizado no envio. O trabalho foi feito com agentes de IA (planejamento e execução em paralelo) sob minha direção e revisão; as horas são minhas, não de máquina.
