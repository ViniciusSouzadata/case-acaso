# O que faz uma pessoa voltar ao assistente em até 7 dias

Vinícius Souza · Desafio técnico Acaso · novembro de 2026

## O trabalho em uma página

| Etapa | O que fiz | O que saiu |
|---|---|---|
| **Pergunta** | O que faz alguém voltar em até 7 dias depois da primeira vez, e quanto disso é efeito do assistente | — |
| **Dado** | WildChat, só Brasil, de abril de 2023 a abril de 2024 | 11.621 conversas, 2.385 IPs |
| **Definições** | Sem login, uma pessoa é um IP mais a família do navegador. Sessão fecha com 30 minutos sem uso. Voltar é abrir nova sessão em até 7 dias | 2.372 novos usuários |
| **Medida** | Taxa de retorno com intervalo de 95% | 23,9% (de 22,2% a 25,6%) |
| **Fatores** | 25 comparações entre pessoas de perfil parecido | 1 se sustenta: a recusa |
| **Entrega** | Base em Postgres, API e painel com 3 telas, sobem com um comando | `docker compose up` |

De cada 100 pessoas que experimentam o assistente, 24 voltam em até 7 dias. Se voltar exigir outro dia, são 17. A resposta honesta para o cliente é "entre 17% e 24%, conforme o que você chama de voltar".

**Achado 1. Quem recebe uma recusa na primeira resposta volta bem menos.** Dos 132 usuários que receberam recusa, 13 voltaram (9,8%). Dos outros 2.240, voltaram 553 (24,7%). Comparando pessoas de perfil parecido, a diferença é de 16,4 pontos, com intervalo de 11,5 a 21,4. É o único comportamento do assistente que resiste a todos os testes que fiz. A decisão que isso sustenta: acompanhar a taxa de recusa como indicador de saúde e testar, de forma controlada, uma recusa que ofereça alternativa. O limite: é comparação, não experimento, e o grupo é pequeno.

**Achado 2. Trocar de modelo não mostrou ganho de retorno.** GPT-4 contra GPT-3.5 dá 2,9 pontos a menos, com intervalo de −8,0 a +2,2. Os dados descartam um ganho acima de 2 pontos. A decisão: não justificar um modelo mais caro por retenção. Se a troca vier por qualidade, medir com teste controlado.

**Achado 3. Queda semanal isolada engana.** A maior queda da série, na semana de 01/05/2023, era efeito do início da coleta: parecia 17,1 pontos e caiu para 7,7 quando tratei o começo da base com folga. A semana de 20/11/2023, quando entrou um modelo novo, caiu 4,9 pontos, dentro da variação normal. De 33 semanas testadas, 1 passou do limite; o acaso sozinho produz cerca de 2. A decisão: o alerta do painel só dispara acima da variação normal.

O que os dados não permitem: provar causa, enxergar efeito menor que 5 pontos e reconhecer a mesma pessoa em outra rede ou outro aparelho.

## 1. Definições e o que muda se eu estiver errado

Recalculei a taxa com cada definição alternativa, usando a mesma função. A oficial é 23,86%.

| Premissa | Escolha | Com a alternativa |
|---|---|---|
| Quem é um usuário | IP + família do navegador, sem versão | só IP: 23,94% · IP + navegador completo: 25,14% |
| Sessão | até 30 min entre o fim de uma conversa e o início da próxima | 60 min: 21,54% |
| Voltar | nova sessão iniciada em até 7 dias (168 h) | só em outro dia: 16,86% |
| O que conta como uso | ao menos 1 pergunta não vazia e 1 resposta | contando as vazias: 23,69% |
| Início da base | os 14 primeiros dias ficam fora, e também quem não completou 7 dias | sem o corte: 24,01% · com 28 dias: 23,70% |
| Tráfego anômalo | IP com 200 ou mais conversas, ou 10 ou mais navegadores, fica fora (11 usuários) | com eles: 24,08% |
| Fuso | America/Sao_Paulo | UTC: mesma taxa; 44 usuários mudam de semana |

A única escolha que move o número de verdade é o que se chama de voltar. As outras mexem menos de 2,5 pontos. Cada decisão tem um registro em `docs/decisoes/` (BDR-01 a BDR-07), com as opções que considerei.

## 2. O que os dados mostram

O uso é muito concentrado. Dos 2.385 IPs, os 24 mais ativos respondem por 41% das conversas, e um só responde por 13,4%. Sem tirar esse tráfego, qualquer média descreveria meia dúzia de robôs.

As conversas são curtas: 56% têm um único turno. Quem tem 4 ou mais mensagens na primeira sessão volta mais (32,9% contra 17,2%), mas isso acontece depois da resposta do assistente. Trato como sinal de interesse, não como fator do assistente.

O retorno por semana varia muito, e a faixa de incerteza de cada ponto tem em média 22 pontos de largura. Boa parte do sobe e desce semanal é ruído. Os gráficos que levaram a essas conclusões estão em `docs/figuras/`.

**Variáveis da primeira experiência.** Modelo, tema, tamanho da pergunta e da resposta, recusa, idioma, dispositivo, período do dia, fim de semana e região. Todas são derivadas na carga (`loader/derivar.py`) e descritas no dicionário do painel.

**Como conferi a classificação por IA.** Rotulei 200 conversas à mão, sem ver a resposta da máquina. As regras de palavras-chave acertavam 81% das recusas e só 37% dos temas. O LLM (Claude Haiku) acertou 92% das recusas e 56% dos temas. Por isso a recusa entra na análise com o rótulo do LLM e o tema fica só como descrição. Essa troca mudou o resultado: com as regras, o efeito da recusa parecia 3,3 pontos e não se distinguia de zero. Detalhe em `docs/validacao_llm.md`.

**Problemas de qualidade.** 141 perguntas vazias, 93 conversas com texto repetido, 175 IPs que mudam, 56 conversas com dado removido pelos autores e detecção de idioma que erra em pergunta curta. O painel lista cada um com o tratamento. As conversas tóxicas foram removidas na origem, e é nelas que as recusas são mais comuns.

**Dados que faltam.** ID de login, versão do produto por data, satisfação declarada e o motivo de a pessoa ter parado.

## 3. O que pesa no retorno

Diferença na taxa de retorno, em pontos percentuais. O ajustado compara pessoas parecidas nos outros fatores, por regressão logística com erro agrupado por IP. Dos 25 efeitos ajustados, só a recusa passa a correção para muitos testes.

| Fator | Bruto | Ajustado (intervalo de 95%) | Leitura |
|---|---:|---|---|
| Recusa na 1ª resposta | −14,8 | **−16,4 (−21,4 a −11,5)** | se sustenta |
| Tema: conversa pessoal | −10,0 | −8,2 (−14,3 a −2,1) | não passa a correção; tema é descritivo |
| Resposta de 301 a 1.000 caracteres | +8,8 | +4,7 (−1,5 a +10,8) | o bruto enganava |
| Modelo GPT-4 contra GPT-3.5 | +0,1 | −2,9 (−8,0 a +2,2) | não se distingue de zero |
| Resposta com mais de 2.500 caracteres | +7,9 | +0,5 (−6,0 a +7,0) | o bruto enganava |
| Idioma diferente do da pergunta | +3,0 | +0,1 (−7,7 a +7,9) | não se distingue de zero |

O efeito da recusa quase não muda quando troco a definição de usuário, a de sessão ou o corte do início da base: fica entre −14,4 e −16,4. As 132 recusas vêm de 131 IPs, então não é um usuário puxando o resultado. Os testes estão em `docs/robustez_recusa.md`.

**Causa ou seleção.** O tamanho da resposta mostra bem o problema: no bruto, resposta mais longa parecia trazer 8 pontos de retorno; comparando pessoas parecidas, sobra quase nada. Era o perfil de quem pergunta, não a resposta. Para modelo e para a troca de modelo padrão em dezembro de 2023, usei um segundo método, que pondera os grupos até ficarem comparáveis, e a leitura foi a mesma. Para a recusa esse segundo método não fecha: com 132 casos não consegui montar um grupo de comparação equilibrado, e digo isso no painel.

**O que isso prova.** Que a recusa anda junto de bem menos retorno. Não prova que a recusa cause a saída: ela pode ser o sinal de um pedido que o produto não atende. Só um teste controlado responde.

## 4. A semana que caiu

O enunciado pede uma semana e a explicação. Comparei cada semana com 4 semanas de base e separei a diferença em duas partes: mudou quem chegou, ou mudou o comportamento de cada tipo de pessoa.

| Semana | Retorno | Base | Diferença | Quem chegou / comportamento | p |
|---|---|---|---:|---|---:|
| 20/11/2023 | 21,5% (n = 65) | 26,4% (n = 197) | −4,9 | −0,4 / −4,4 | 0,43 |
| 01/05/2023 | 16,7% (n = 84) | 24,4% (n = 340) | −7,7 | −0,6 / −7,1 | 0,13 |

Nas duas, quase toda a diferença é de comportamento, não de público. E nenhuma das duas passa do que a variação normal produz. A semana de 01/05 me enganou na primeira leitura: comparada com as duas semanas anteriores, que eram o começo da coleta, parecia a maior queda da série.

## 5. O painel

| Tela | Pergunta que responde | Gráfico e por quê |
|---|---|---|
| Retenção | De cada 100 pessoas, quantas voltam em 7 dias, e isso está mudando? | Linha por semana com faixa de incerteza, para ninguém ler ponto solto como tendência. Cascata para separar público de comportamento |
| O que faz voltar | Quais fatores pesam, e quanto é efeito do assistente? | Um ponto por fator com o intervalo. O que cruza o zero se vê de relance |
| Confiança nos dados | Posso confiar nestes números? | Tabelas: última carga, conferência com a origem, problemas de qualidade e dicionário |

Todo número tem definição, fórmula, denominador, período e a consulta SQL, a um clique. Quando a amostra é pequena, o painel escreve "amostra pequena" no lugar do número. Semanas que ainda não completaram 7 dias aparecem hachuradas, nunca como queda. O painel mostra só agregados. Texto de conversa, IP e navegador não aparecem em nenhuma tela nem na API, e o texto de conversa nem entra no banco.

## 6. Arquitetura e custo

O arquivo bruto passa por uma carga em Python, que grava no Postgres. A análise lê dessa base e grava os resultados em tabelas. A API, em Next.js, lê só as tabelas finais, com um usuário de banco que só tem permissão de leitura. Os indicadores são calculados na carga e a API guarda as respostas em cache até a carga seguinte. Diagrama, modelo da base e lista de endpoints estão em `docs/arquitetura/arquitetura.md`.

Na AWS, o desenho usa RDS PostgreSQL, containers para o app e a carga, balanceador, S3 para o bruto e Bedrock para o LLM. O custo estimado é de **US$ 54 por mês**, com preços da tabela oficial da AWS consultados em 12/11/2026. O LLM custou US$ 0,24 para classificar 2.944 conversas, cerca de US$ 0,08 por mil. É um desenho com custo calculado. Não implantei.

Para outros países, o país já é parâmetro na base e na API. Os textos do painel ficam em arquivo separado por idioma, o fuso é configurado por país e a comparação entre países usa a mesma separação entre público e comportamento da seção 4.

## 7. Como eu saberia que um número está errado

A cada carga, o programa refaz 9 contagens direto do arquivo bruto e compara com a base. Hoje a diferença é zero nas 9. Cada carga deixa um registro com arquivo de origem, linhas lidas, gravadas e rejeitadas. Cada resposta da API deixa um log com identificador, tempo e versão dos dados, e a tela mostra esse identificador quando dá erro. O caminho de investigação é tela, log, consulta, tabela, carga, arquivo.

As definições são travadas por testes sobre uma base pequena, inventada, em que eu sei a resposta certa: retorno em 6 dias e 23 horas conta, em 7 dias e 1 minuto não; trocar a versão do navegador não cria usuário novo. Quebrei as regras de propósito para ver se os testes pegavam. Um deles não pegava a troca de `<=` por `<` na janela de 7 dias, e acrescentei o teste que faltava.

Até produção, a mesma imagem passa por local, homologação e produção, e nunca se constrói em produção. As mudanças de banco são arquivos SQL numerados, cada um com o passo inverso. Depois de cada implantação rodam a verificação de saúde e a conferência com a origem, e só então entra tráfego.

Três ressalvas. O envio automático do alerta de divergência está descrito, não construído. Os passos inversos das mudanças de banco estão escritos, mas não foram executados. E a esteira de integração contínua está configurada, mas ainda não rodou.

## 8. O incidente: a retenção caiu de 31% para 18%

**Por onde eu começaria.** Pela tabela do enunciado, comparando as duas fontes semana a semana. Quem voltou fica estável nas duas: 366 no painel e 352 no relatório. Quem chegou explode só no painel: 2.034 contra 1.172. A queda não é de comportamento, é de contagem de usuários novos.

**Em qual camada.** Na carga, na regra que define o usuário. O relatório conta por IP; a carga conta por IP mais o texto completo do navegador. Reproduzi o mecanismo no dado real: por IP são 2.385 usuários; por IP mais navegador completo são 2.895, 21% a mais, e um único IP chega a ter 35 navegadores. A consulta de confirmação está em `docs/incidente/confirmacao.sql`.

**O trecho e a correção.** A linha é `chave = f"{hashed_ip}|{user-agent}"`. Cada atualização de navegador vira uma pessoa nova. A correção escrita está em `docs/incidente/correcao/`: identidade por uma regra única, a mesma em todo o sistema, e carga dentro de transação. O código de referência tem outros defeitos sem relação com a queda, listados no mesmo lugar.

**O que mais fazer.** Reprocessar o histórico com a regra corrigida. Alinhar a definição de usuário com o time de dados, porque a causa de fundo são duas definições e nenhuma conferência entre elas. Ligar a conferência automática da seção 7. E manter o teste que escrevi para esse caso, que falha se alguém voltar à chave antiga.

**O que eu diria à gerente de produto.** Durante: "A queda é quase certamente de medição. O número de pessoas que voltaram não mudou, só o de pessoas que chegaram. Não tome decisão em cima do 18%. Volto com a causa confirmada até tal hora." Depois: "Uma troca de navegador estava contando como usuário novo. Corrigimos, a retenção daquela semana é tanto, e os números que você já apresentou mudam assim. Agora a contagem é conferida automaticamente com o relatório do time de dados."

## 9. Riscos e decisões que não são minhas

| Risco | Decisão a levar ao time e ao cliente |
|---|---|
| Sem login, a identidade erra para os dois lados | Qual é a definição oficial de usuário |
| O dado tem texto de conversa e IP | Política de retenção e base legal; o que pode ir para um LLM |
| Mudar o que é voltar muda o número oficial | Quem aprova mudança de definição e como se comunica |
| Com 2.400 usuários só se enxerga efeito grande | Qual tamanho de efeito vale uma ação, e se vale um teste no produto |
| O custo do LLM cresce com a base | Orçamento e quem aprova |
| Carga em lote | Prazo de atualização e o que o painel mostra quando atrasa |

## 10. Sugestões

Para o assistente: revisar as recusas desnecessárias e testar uma recusa que ofereça alternativa. Não trocar de modelo esperando retenção. Para o painel, depois de ver os dados: mostrar a taxa de recusa ao lado da retenção, mostrar "voltou em outro dia" ao lado da taxa oficial, e deixar a conferência com a origem visível para o cliente.

## 11. O que eu faria diferente

Com ID de login, refaria tudo com a identidade real; o código recalcula com um comando. Pediria a versão do produto por data, para explicar as semanas em vez de só descrevê-las. Faria o teste controlado de recusa. Implantaria de fato na AWS. E deixaria de regravar a base inteira a cada carga, passando para carga incremental.

## 12. Uso de IA e horas

Usei o Claude, pelo Claude Code, para planejar, escrever código e testes, e um LLM para classificar tema e recusa. As definições, a escolha dos métodos e as conclusões são minhas. Conferi o trabalho da IA de três formas: 200 conversas rotuladas por mim, uma base inventada de resposta conhecida e a conferência do bruto com a base.

O que corrigi ou descartei: a primeira versão do cálculo de efeito estimava 7,0 pontos onde o certo era 10,1, e o teste pegou. O classificador por palavras-chave foi descartado depois da validação. Um segundo LLM foi descartado por deixar 40% dos itens sem resposta. A consulta principal levava 12 segundos e passou a 0,33. Mais casos em `docs/conferi_da_ia.md`.

Foram cerca de **[total] horas** minhas, acima das 12 sugeridas, porque rotulei a validação à mão e entreguei o painel completo.

## Onde está cada item do enunciado

| Item do enunciado | Onde está |
|---|---|
| 1. Pergunta, fatores, causa e seleção | página 1 e seção 3 |
| 2.1 Identidade sem ID de usuário | seção 1 · BDR-01 |
| 2.2 Base analítica, AWS e custo, dados pessoais | seções 5 e 6 · `docs/arquitetura/arquitetura.md` |
| 2.3 Premissas | seção 1 · `docs/decisoes/` |
| 3. Um comando, telas com dados reais, ADRs e BDRs | `README.md` · `docs/decisoes/` |
| 3.1 Definições, variáveis, validação da IA, qualidade, EDA, sugestões | seções 1, 2 e 10 · `docs/figuras/` |
| 3.2 Efeitos com intervalo, confusão, a semana, três achados | página 1, seções 3 e 4 |
| 3.3 Telas, indicadores com SQL, arquitetura, endpoints, outros países, desempenho | seções 5 e 6 · `arquitetura.md` · `docs/desempenho.md` · tela Confiança nos dados |
| 4.1 Registros por camada, divergência, testes, caminho até produção | seção 7 · `arquitetura.md` |
| 4.2 Incidente, as cinco perguntas | seção 8 · `docs/incidente/` |
| 4.3 Riscos e decisões | seção 9 |
| 5. Uso de IA e horas | seção 12 · `docs/conferi_da_ia.md` |
