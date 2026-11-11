# Desempenho da API

Medido em 2026-11-11. 50 chamadas por rota, em milissegundos.

- **Frio**: cache em memória limpo antes de cada chamada, então cada chamada consulta o banco.
- **Quente**: resposta já no cache (mesma rota, mesmos parâmetros, mesmo lote).
- Como foi medido: os handlers das rotas rodam no próprio processo (`scripts/medir_api.ts`), contra um Postgres 16 local em Docker (WSL2), com o papel `app_ro`. **Inclui** banco, montagem do envelope e validação dos parâmetros; **não inclui** rede nem o servidor HTTP do Next.
- Toda chamada, mesmo a quente, faz uma leitura leve do último lote (para saber se o cache ainda vale).
- Máquina de desenvolvimento com pouca memória: os números servem de ordem de grandeza, não de garantia.

| Rota | frio p50 | frio p95 | quente p50 | quente p95 |
|---|---:|---:|---:|---:|
| `/api/retencao/resumo` | 4.9 | 15.6 | 2.3 | 7.2 |
| `/api/retencao/coortes` | 4.9 | 8.6 | 2.3 | 4.9 |
| `/api/retencao/coortes?granularidade=mes` | 4.3 | 9.3 | 1.9 | 4.9 |
| `/api/retencao/sensibilidade` | 4.2 | 9.3 | 2.5 | 5.2 |
| `/api/dicionario` | 4.4 | 10.1 | 2.9 | 5.9 |
| `/api/fatores/efeitos` | 5.3 | 10.1 | 3.0 | 4.0 |
| `/api/fatores/segmentos?variavel=era_modelo` | 4.2 | 8.6 | 2.8 | 9.5 |
| `/api/fatores/balanco?tratamento=modelo_familia` | 4.4 | 11.8 | 2.5 | 7.3 |
| `/api/semana/decomposicao?semana=2023-05-01` | 5.5 | 16.4 | 3.0 | 9.3 |
| `/api/achados` | 3.5 | 7.8 | 1.8 | 3.9 |
| `/api/qualidade` | n/d | n/d | n/d | n/d |

Como repetir: `cd app && DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx tsx ../scripts/medir_api.ts`.
Em produção as mesmas métricas saem do log JSON de uma linha por requisição (`duracao_ms`, `cache`) no CloudWatch Logs Insights, e o cabeçalho `Server-Timing` traz banco e total em cada resposta.
