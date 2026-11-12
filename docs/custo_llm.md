# Custo do classificador LLM (medido)

Gerado por `scripts/custo_llm.py` a partir do log de chamadas (sem texto de conversa). Todos os números vêm do log; projeções são custo medido por conversa × tamanho da base.

| Modelo | Chamadas | Conversas enviadas | Tokens entrada | Tokens saída | Custo medido | Custo por 1.000 conversas | Base Brasil (11.545) | WildChat inteiro (838 mil) | Chamadas com falha/parcial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| openrouter:amazon/nova-lite-v1 | 29 | 290 | 65933 | 7344 | US$ 0,01 | US$ 0,02 | US$ 0,23 | US$ 16,52 | 17 |
| openrouter:anthropic/claude-haiku-5.5 | 295 | 2944 | 937746 | 291112 | US$ 0,24 | US$ 0,08 | US$ 0,94 | US$ 68,13 | 15 |

## Alavancas de custo (o que reduz token sem perder a leitura)
- **Amostra validada antes de escalar:** 200 conversas rotuladas por pessoa decidem o modelo; só depois roda a base.
- **Só a 1ª conversa de cada usuário** que entra em algum número (união das 4 definições), não a base inteira.
- **Truncamento** da pergunta e da resposta (600 caracteres, a mesma régua do humano).
- **Lote** de 10 conversas por chamada (um prompt de instruções para dez itens).
- **Cache:** conversa já classificada (modelo + versão do prompt) nunca é reenviada.
- **Teto** `LLM_TETO_USD` (padrão US$ 3,00): a execução para ao atingir.
- **Modelo barato o bastante** escolhido pelo kappa de tema, com custo como desempate (ver `docs/validacao_llm.md`).
