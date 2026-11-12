# Robustez do efeito da recusa (R1–R5)

Gerado por `scripts/robustez_recusa.py`. Só agregados.

## R1 — Efeito ajustado da recusa por definição

| Definição | n | recusas | efeito ajustado (p.p.) | IC 95% | p |
|---|---:|---:|---:|---|---:|
| oficial | 2372 | 132 | -16.4 | -21.4 a -11.5 | 0.0000 |
| so_ip | 2239 | 129 | -16.4 | -21.4 a -11.3 | 0.0000 |
| ip_ua_completo | 2657 | 144 | -14.4 | -20.6 a -8.2 | 0.0000 |
| sessao_60min | 2372 | 132 | -15.4 | -19.9 a -10.8 | 0.0000 |
| burn-in 28 dias | 2232 | 123 | -16.3 | -21.4 a -11.1 | 0.0000 |

## R2 — Recusa × tema (definição oficial)

| Tema (LLM) | n | recusas | % recusa | retorno com recusa | retorno sem recusa | efeito bruto (p.p.) | IC 95% (Newcombe) |
|---|---:|---:|---:|---:|---:|---:|---|
| criação/ficção e roleplay | 285 | 27 | 9.5% | 7.4% | 28.7% | -21.3 | -29.2 a -4.5 |
| outros/indefinido | 161 | 25 | 15.5% | 8.0% | 22.8% | -14.8 | -24.5 a +3.3 |
| programação/TI | 280 | 24 | 8.6% | 8.3% | 23.0% | -14.7 | -22.9 a +3.4 |
| informação geral/curiosidade | 437 | 20 | 4.6% | 20.0% | 24.7% | -4.7 | -17.4 a +17.3 |
| trabalho/negócios | 208 | 16 | 7.7% | 6.2% | 34.4% | -28.1 | -36.8 a -5.1 |
| conversa pessoal/conselho | 489 | 7 | 1.4% | (poucas recusas) | | | |
| estudo/dever de casa | 296 | 7 | 2.4% | (poucas recusas) | | | |
| escrita e tradução | 216 | 6 | 2.8% | (poucas recusas) | | | |

Nota: o modelo ajustado de R1 já inclui o tema como covariável.

## R3 — Concentração por IP

- Recusas: 132; IPs distintos com recusa: 131; maior IP: 2 recusas; os 10 maiores somam 11.
- Efeito ajustado sem os 10 IPs com mais recusas (n = 2361, recusas = 121): -16.4 p.p. (IC -21.5 a -11.2; p = 0.0000).

## R4 — Erro do classificador (não diferencial)

- Precisão ponderada 0.811, revocação ponderada 0.861 (validação nas 200).
- Retorno observado: rotulado recusa 9.8%, rotulado não-recusa 24.7% (bruto -14.8 p.p.).
- Corrigindo a mistura (cada grupo rotulado mistura os dois tipos reais): retorno de quem de fato recusou 6.4%, de quem não 24.8% → diferença -18.5 p.p.; fator de correção 1.24×.
- Leitura: erro de classificação que não depende do desfecho **encolhe** o efeito em direção a zero; o efeito observado tende a ser um limite inferior em módulo. Vale só se o erro for não diferencial: se o LLM errar mais em quem some (por exemplo, recusa suave em pedido difícil), o viés pode ir para qualquer lado.

## R5 — Recusa por regras nos mesmos 2372 usuários

| Rótulo | recusas | retorno com recusa | retorno sem | bruto (p.p.) | IC Newcombe | ajustado (p.p.) | IC 95% | p |
|---|---:|---:|---:|---:|---|---:|---|---:|
| LLM (Haiku 5.5) | 132 | 9.8% | 24.7% | -14.8 | -19.2 a -8.3 | -16.4 | ver R1 | |
| Regras | 153 | 22.2% | 24.0% | -1.8 | -7.9 a +5.7 | -3.3 | -10.1 a +3.5 | 0.3380 |

Concordância: as duas marcam 90; só LLM 42; só regras 63.

## R6 — Recusa com "voltou em outro dia" como retorno

Retorno geral nessa regra: 400 de 2372 (16.86%).

| Definição de retorno | voltaram com recusa | voltaram sem recusa | bruto (p.p.) | IC Newcombe | ajustado (p.p.) | IC 95% | p |
|---|---|---|---:|---|---:|---|---:|
| oficial (nova sessão em 7 dias) | 13 de 132 (9.8%) | 553 de 2240 (24.7%) | -14.8 | -19.2 a -8.3 | -16.4 | -21.4 a -11.5 | 0.0000 |
| outro dia | 9 de 132 (6.8%) | 391 de 2240 (17.5%) | -10.6 | -14.2 a -4.8 | -11.5 | -15.7 a -7.3 | 0.0000 |

## R7 — Contagens cruas (definição oficial)

Voltaram 13 de 132 com recusa e 553 de 2240 sem recusa.
