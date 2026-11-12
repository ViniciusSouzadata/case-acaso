# Desempenho da API

Medido em 2026-11-11. 50 chamadas por rota, em milissegundos.

- **Frio**: cache em memória limpo antes de cada chamada, então cada chamada consulta o banco.
- **Quente**: resposta já no cache (mesma rota, mesmos parâmetros, mesmo lote).
- Como foi medido: os handlers das rotas rodam no próprio processo (`scripts/medir_api.ts`), contra um Postgres 16 local em Docker (WSL2), com o papel `app_ro`. **Inclui** banco, montagem do envelope e validação dos parâmetros; **não inclui** rede nem o servidor HTTP do Next.
- Toda chamada, mesmo a quente, faz uma leitura leve do último lote (para saber se o cache ainda vale).
- Máquina de desenvolvimento com pouca memória: os números servem de ordem de grandeza, não de garantia.

| Rota | frio p50 | frio p95 | quente p50 | quente p95 |
|---|---:|---:|---:|---:|
| `/api/retencao/resumo` | 4.6 | 9.1 | 3.1 | 7.2 |
| `/api/retencao/coortes` | 5.6 | 13.1 | 2.4 | 4.3 |
| `/api/retencao/coortes?granularidade=mes` | 3.7 | 6.6 | 2.4 | 5.2 |
| `/api/retencao/sensibilidade` | 5.9 | 14.3 | 4.0 | 9.3 |
| `/api/dicionario` | 7.0 | 14.5 | 3.3 | 8.7 |
| `/api/fatores/efeitos` | 7.2 | 13.7 | 3.0 | 8.3 |
| `/api/fatores/segmentos?variavel=era_modelo` | 4.0 | 8.3 | 3.0 | 9.5 |
| `/api/fatores/balanco?tratamento=modelo_familia` | 5.0 | 18.2 | 2.0 | 7.4 |
| `/api/semana/decomposicao?semana=2023-05-01` | 5.0 | 9.7 | 2.8 | 11.7 |
| `/api/achados` | 4.2 | 13.7 | 2.2 | 9.8 |
| `/api/qualidade` | 10.3 | 40.4 | 2.7 | 14.1 |

Como repetir: `cd app && DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso npx tsx ../scripts/medir_api.ts`.
Em produção as mesmas métricas saem do log JSON de uma linha por requisição (`duracao_ms`, `cache`) no CloudWatch Logs Insights, e o cabeçalho `Server-Timing` traz banco e total em cada resposta.
