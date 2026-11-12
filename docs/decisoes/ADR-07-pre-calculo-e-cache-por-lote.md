# ADR-07 — Pré-cálculo e cache invalidado por lote de carga
**Atende:** C-31

## Contexto
A tela precisa responder rápido, e o que ela mostra só muda quando entra uma carga nova.

## Opções consideradas
- Calcular na hora a cada requisição.
- **Pré-calcular em `mart.agg_*` e `resultado.*` e guardar em cache na API, invalidado quando o lote de carga muda.**

## Escolha
Segunda opção. A API consulta tabelas já agregadas; o cache expira ao detectar um novo `lote_id` (registro em `ops.lote_carga`) e por tempo máximo.

## Consequências
- O custo de calcular fica na carga (segundos), não na requisição.
- O tempo de resposta é medido por requisição (cabeçalho `Server-Timing`), e os números estão em `docs/desempenho.md`.
- Risco: cache mostrar número antigo. Mitigação: invalidação pelo lote e rodapé da tela com data e versão dos dados.

## Como defender
- **Por quê:** o dado é de "lote", então cache por lote é correto, não só rápido.
- **O que descartei:** cache por tempo fixo apenas (serviria número velho depois de uma recarga).
- **O que mudaria minha decisão:** dados em tempo real; aí viria uma fila de atualização incremental.
