# Validação do classificador LLM (200 conversas rotuladas)

Gerado por `python -m classificador.validar_llm`; só agregados.
Truncamento 600 caracteres, lote de 10, prompt or-1.0.0, temperatura 0.

| Classificador | Tema acurácia (crua / pond.) | Tema kappa | Recusa acurácia | Recusa kappa | Recusa precisão (crua / pond.) | Recusa revocação (crua / pond.) | Falhas | Custo (200) |
|---|---|---|---|---|---|---|---|---|
| regras (linha de base) | 36,5% / 31,8% | 0,27 | 81,0% | 0,37 | 32,0% / 30,2% | 80,0% / 48,8% | — | — |
| openrouter:anthropic/claude-haiku-5.5 | 56,0% / 59,3% | 0,48 | 92,0% | 0,59 | 58,3% / 81,1% | 70,0% / 86,1% | 0/200 em fallback | US$ 0,0201 |
| openrouter:amazon/nova-lite-v1 | 32,5% / 34,6% | 0,26 | 88,0% | 0,45 | 43,3% / 42,5% | 65,0% / 53,7% | 80/200 em fallback | US$ 0,0057 |
