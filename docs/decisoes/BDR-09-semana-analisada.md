# BDR-09 — Qual semana explicar (e por que a maior queda era artefato)
**Atende:** C-25, C-24

## Contexto
O case pede uma semana em que o retorno caiu e o que explica: mudança de público (mix) ou de taxa dentro do público.

## Opções consideradas
Rodei as 3 candidatas com amostra suficiente. Cada uma é comparada com 4 semanas de coorte **limpas**: só entram na base semanas que começam pelo menos 28 dias depois do primeiro dado da coleta (09/04/2023). A de 01/05 não tem base anterior limpa e foi comparada com as 4 seguintes.

| Semana | Retorno | Base | Variação | Mix / taxa | p |
|---|---|---|---:|---|---:|
| **20/11/2023** (a do case) | 21,5% (n=65) | 26,4% (n=197), 4 semanas anteriores | −4,9 pontos | −0,4 / −4,4 | 0,43 |
| 17/07/2023 | 9,1% (n=33) | 22,5% (n=178), 4 semanas anteriores | −13,4 | −0,5 / −12,9 | 0,08 |
| 01/05/2023 | 16,7% (n=84) | 24,4% (n=340), 4 semanas **seguintes** | −7,7 | −0,6 / −7,1 | 0,13 |

## Escolha
**Semana principal: 20/11/2023.** É a que o contexto do caso aponta (chegada do GPT-4 Turbo). A queda é de −4,9 pontos, quase toda de taxa, **dentro do ruído** (p = 0,43).

**01/05/2023 é o caso de artefato.** Na primeira versão (base = as 2 semanas anteriores, 33,8%) ela era a maior queda da série: −17,1 pontos, p = 0,013. Isso desaparece quando o início da coleta é tratado com folga: com burn-in de 28 dias, as duas semanas de base (17/04 e 24/04) caem fora e a semana de 01/05 fica com n = 18; contra as 4 semanas seguintes a queda é de −7,7 pontos, p = 0,13.

## Consequências
- Definição oficial **não muda**: burn-in de 14 dias (pré-registrado), 566 / 2.372 (23,86%). O burn-in de 28 dias dá 2.232 elegíveis e 23,70% (checado ao lado por `scripts/burnin_14_vs_28.py`, não gravado como definição).
- **Regra nova** (decomposição e alerta do dashboard): semana de base precisa começar pelo menos 28 dias depois do primeiro dado. A marca `inicio_coleta` fica em `mart.agg_retencao_periodo` (semanas 17/04, 24/04 e 01/05/2023; mês de abril/2023), calculada do mínimo da base, sem data fixa.
- Testando todas as semanas com amostra suficiente e base limpa: 33 testadas, 1 com p < 0,05; o acaso sozinho produz cerca de 2. Quedas semanais isoladas não sustentam conclusão.
- Nas três, a queda é de **taxa** (as pessoas voltaram menos), não de mix.

## Como defender
- **Por quê:** a semana mais extrema entre 35 era um efeito de como a coleta começou, não do produto; o método mostra isso em vez de esconder.
- **Cautela declarada:** escolher a semana mais extrema infla a chance de achar algo; por isso o documento mostra quantas semanas passariam por acaso.
- **O que mudaria minha decisão:** saber o que mudou no produto em 01/05 (canal ou modelo) e ter a data de início real da coleta do dado.
