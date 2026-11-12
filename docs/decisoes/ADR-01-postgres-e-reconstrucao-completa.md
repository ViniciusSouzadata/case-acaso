# ADR-01 — Postgres como base analítica e reconstrução completa
**Atende:** C-10, C-14, C-29

## Contexto
O dashboard não pode ler a base bruta (C-10). A base analítica precisa ser desenhada, populada pelo projeto e subir com um comando.

## Opções consideradas
- Ler o arquivo bruto direto (DuckDB) na API.
- **Postgres com camadas:** `stg` (carga, acesso restrito), `mart` (indicadores) e `resultado` (saída da análise), mais `ops` (parâmetros, lotes, reconciliação).
- Warehouse gerenciado.

## Escolha
Postgres 16 no Docker Compose, com **reconstrução completa dos marts a cada carga**: as tabelas novas são montadas ao lado e trocadas na mesma transação, então quem lê nunca vê tabela vazia.

## Consequências
- Com 11.621 conversas, reconstruir tudo leva segundos (transformação de 118 s para 2,8 s depois de eu achar uma subconsulta repetida por usuário).
- Não há atualização incremental; com milhões de linhas, isso mudaria (ADR-07).
- O mesmo SQL de cálculo é a "função única" de retenção usada pelo oficial e por todas as sensibilidades, então as variações não divergem.

## Como defender
- **Por quê:** o volume é pequeno, e reconstruir é mais simples de provar correto (a reconciliação confere: 9 métricas, diferença 0).
- **O que descartei:** DuckDB na API (mistura análise e serviço, sem papéis de acesso); warehouse gerenciado (custo e complexidade sem necessidade neste volume).
- **O que mudaria minha decisão:** volume na casa de dezenas de milhões de conversas, ou cargas de hora em hora.
- **O que faria diferente:** carga incremental por lote, com o mesmo teste de reconciliação.
