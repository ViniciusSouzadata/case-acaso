# ADR-09 — Classificar tema e recusa: regras, LLM e como conferi
**Atende:** C-17, C-18, C-11

## Contexto
O cliente quer saber se o assunto da conversa e a recusa do assistente afetam o retorno. O dado não traz nenhum dos dois pronto.

## Opções consideradas
1. **Regras** de palavra-chave (sem LLM, sem credencial).
2. **LLM no Amazon Bedrock** (cumpre a restrição do case: LLM na AWS).
3. **LLM por OpenRouter** (alternativa autorizada pela Acaso em 11/11, chave de US$ 10 que expira em 18/11).

## Escolha
Interface única `classificar`, três provedores (regras, Bedrock, OpenRouter). **Principal para a entrega: Bedrock. Reserva testada: OpenRouter.** Na prática, **a rodada foi feita pela OpenRouter**: no Bedrock da minha conta toda chamada de inferência (Converse e InvokeModel, 4 modelos, id direto e perfil de inferência) devolveu `ValidationException: Operation not allowed` (HTTP 400), embora as credenciais valham (STS ok) e o Bedrock liste 98 modelos. É padrão de conta sem acesso de inferência liberado; precisa de ação no console da AWS, que não está feita. O código do Bedrock está escrito e testado sem rede, **mas nunca rodou de verdade**. O padrão do compose, sem credencial, é o seed versionado (origem registrada por linha em `tema_origem` e `recusa_origem`).

## Como conferi (validação humana)
200 conversas rotuladas por mim, sem ver o que a máquina respondeu (amostra estratificada pela previsão das regras). Contra o `regras`:

| | Acurácia | Kappa |
|---|---:|---:|
| Tema | 36,5% (31,8% ponderada pela população) | 0,27 |
| Recusa | 81,0% | 0,37 |

Recusa por regras: pega 80,0% das recusas reais na amostra, **48,8% ponderada pela população**, e só 32,0% do que marca como recusa é recusa (30,2% ponderada). Conclusão: com regras, **tema é descritivo e recusa é aproximada**.

## Números do LLM (mesmas 200, prompt `or-1.0.0`, truncamento 600, lote 10, temperatura 0)
Cada classificador é avaliado nas 200 completas (`seeds/validacao_previsoes.csv`; as regras são aplicadas na hora e o LLM vem do cache).

| Classificador | Tema acurácia (ponderada) | Tema kappa | Recusa acurácia | Recusa kappa | Recusa precisão (pond.) | Recusa revocação (pond.) | Falhas | Custo (200) |
|---|---|---:|---:|---:|---|---|---|---|
| Regras | 36,5% (31,8%) | 0,27 | 81,0% | 0,37 | 32,0% (30,2%) | 80,0% (48,8%) | — | — |
| **Claude Haiku 5.5** (escolhido) | 56,0% (59,3%) | 0,48 | 92,0% | 0,59 | 58,3% (81,1%) | 70,0% (86,1%) | 0 de 200 | US$ 0,0201 |
| Amazon Nova Lite (descartado) | 32,5% (34,6%) | 0,26 | 88,0% | 0,45 | 43,3% (42,5%) | 65,0% (53,7%) | 80 de 200 | US$ 0,0057 |

- **Por que Haiku 5.5:** kappa de tema 0,48 contra 0,27 das regras; recusa com precisão ponderada de 81% contra 30%. Ainda é "moderado": tema continua descritivo.
- **Por que descartei o Nova Lite:** em 17 de 29 chamadas devolveu texto sem JSON válido (40% dos itens caíram em fallback) e, nos itens válidos, o kappa de tema não passou o das regras. Fica como material de sustentação de agentes (saída estruturada falha por modelo, a validação por item pega).
- **Rodada completa (Haiku 5.5, OpenRouter):** 2.657 primeiras conversas (união das 4 definições de usuário); 2.647 classificadas pelo LLM (99,6%), 10 em fallback (um lote que devolve resposta vazia, tentado 3 vezes); 4 erros de tempo esgotado no log; custo **US$ 0,24** (≈US$ 0,08 por 1.000 conversas; a base Brasil inteira, 11.545 conversas, ≈US$ 0,94; o WildChat inteiro, 838 mil, ≈US$ 68). Detalhe: `docs/custo_llm.md`, `docs/validacao_llm.md`.
- **O que o rótulo mudou:** o efeito da recusa passou de −3,3 p.p. (IC −10,1 a +3,5, rótulo por regras) para −16,4 (−21,4 a −11,5, rótulo do LLM) no mesmo conjunto de usuários; as regras marcavam 63 usuários que o LLM não considera recusa e perdiam 42 que o LLM marca. O sinal aguenta nas 4 definições e com burn-in de 28 dias (`docs/robustez_recusa.md`). Continua observacional.
- **Não medido:** a concordância entre Bedrock e OpenRouter (o Bedrock não roda).

## Cuidados
Só pergunta e resposta truncadas em 600 caracteres saem do computador, sem ID, IP ou user-agent; o texto é tratado como dado, não instrução (há muito jailbreak no dataset); saída em JSON validada por item; falha cai em `regras` e fica marcada; teto de custo e cache por conversa. Dataset público e já anonimizado; **com dado de cliente, só Bedrock dentro da conta**.

## Como defender
- **Por quê:** medir a máquina contra gente é o que torna o número defensável.
- **O que descartei:** ajustar as regras olhando a matriz de confusão (seria ajustar ao gabarito e invalidar a validação); fundir classes (os erros se espalham por quase todas).
- **O que mudaria minha decisão:** kappa do LLM abaixo do das regras, ou custo por 1.000 conversas fora do orçamento; ou o Bedrock liberado, quando a rodada deve ser refeita por ele (≈US$ 1,2) para comparar os dois caminhos.
