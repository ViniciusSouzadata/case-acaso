# ADR-09 — Classificar tema e recusa: regras, LLM e como conferi
**Atende:** C-17, C-18, C-11

## Contexto
O cliente quer saber se o assunto da conversa e a recusa do assistente afetam o retorno. O dado não traz nenhum dos dois pronto.

## Opções consideradas
1. **Regras** de palavra-chave (sem LLM, sem credencial).
2. **LLM no Amazon Bedrock** (cumpre a restrição do case: LLM na AWS).
3. **LLM por OpenRouter** (alternativa autorizada pela Acaso em 11/11, chave de US$ 10 que expira em 18/11).

## Escolha
Interface única `classificar`, três provedores. **Principal para a entrega: Bedrock. Reserva testada: OpenRouter.** O padrão do compose, sem credencial, é o seed versionado (origem registrada por linha em `tema_origem`).

## Como conferi (validação humana)
200 conversas rotuladas por mim, sem ver o que a máquina respondeu (amostra estratificada pela previsão das regras). Contra o `regras`:

| | Acurácia | Kappa |
|---|---:|---:|
| Tema | 36,5% (31,8% ponderada pela população) | 0,27 |
| Recusa | 81,0% | 0,37 |

Recusa por regras: pega 80,0% das recusas reais na amostra, **48,8% ponderada pela população**, e só 32,0% do que marca como recusa é recusa (30,2% ponderada). Conclusão: com regras, **tema é descritivo e recusa é aproximada**.

## Números do LLM
**A preencher após a rodada:** acurácia e kappa de tema e de recusa por modelo (Bedrock e OpenRouter), taxa de falha, concordância entre os dois caminhos, tokens e custo (`docs/validacao_llm.md`, `docs/custo_llm.md`).

## Cuidados
Só pergunta e resposta truncadas em 600 caracteres saem do computador, sem ID, IP ou user-agent; o texto é tratado como dado, não instrução (há muito jailbreak no dataset); saída em JSON validada por item; falha cai em `regras` e fica marcada; teto de custo e cache por conversa. Dataset público e já anonimizado; **com dado de cliente, só Bedrock dentro da conta**.

## Como defender
- **Por quê:** medir a máquina contra gente é o que torna o número defensável.
- **O que descartei:** ajustar as regras olhando a matriz de confusão (seria ajustar ao gabarito e invalidar a validação); fundir classes (os erros se espalham por quase todas).
- **O que mudaria minha decisão:** kappa do LLM abaixo do das regras, ou custo por 1.000 conversas fora do orçamento.
