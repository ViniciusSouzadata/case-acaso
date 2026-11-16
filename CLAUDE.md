# Case Acaso — Retenção de um assistente de IA

Case técnico do Vinícius para a vaga de Data Analyst Pleno na Acaso. Entrega: seg 16/11/2026. Metodologia: TLC Spec-Driven (Waldemar Neto) + BSPA.

## SPEC-CHECK — ler antes de qualquer alteração, nesta ordem
1. `.specs/project/STATE.md` — fase atual, decisões, blockers
2. `.specs/project/PROJECT.md` — princípios inegociáveis e "o que NÃO fazer"
3. `.specs/project/ROADMAP.md` — milestones e regras de sequência
4. `.specs/features/<milestone>/spec.md`, `design.md` e `tasks.md` da task que você recebeu

## Papéis
- **Planejamento** (specs, design, tasks, auditoria): modelo de planejamento. Não escreve código de produção.
- **Execução** (código, testes): Sonnet, **uma task por vez**, exatamente como descrita em `tasks.md`.

## Regras de execução
1. Implemente só a task recebida. Não antecipe outras tasks nem "melhore" o que não foi pedido.
2. O `design.md` é contrato: nomes de tabelas, colunas, endpoints e campos são exatamente os de lá. Se o design estiver errado ou incompleto, **pare e reporte** — não improvise nem altere a spec.
3. A task só termina quando o **Done when** e os **Tests** foram demonstrados de verdade (rodados, com a saída no relatório). "Deve funcionar" não vale.
4. Ao terminar: marque `[x]` na task, e devolva um relatório curto: o que foi feito, arquivos tocados, saída dos testes, desvios do design, dúvidas.
5. Não edite `.specs/` além do `[x]` da sua task. Fatos novos vão no relatório; o planejador atualiza o STATE.

## Knowledge Verification Chain
- **Não invente biblioteca, função, parâmetro ou versão.** Antes de usar uma API que você não tem certeza, confira na documentação instalada (`pip show`, `--help`, `node_modules`) ou rode um teste mínimo.
- DuckDB aqui é 2.x: lambda é `lambda t: ...` (a seta `->` foi removida) e relações não têm `fetchone()` (use `fetchall()`).
- Se algo falhar duas vezes pelo mesmo motivo, pare e reporte em vez de tentar variações às cegas.

## Princípios que nenhuma task pode violar
- Nenhum texto de conversa, `hashed_ip` ou user-agent em `mart.*`, `resultado.*`, na API ou na tela. Texto de conversa não entra no Postgres.
- A aplicação lê só `mart.*` e `resultado.*`, com o papel `app_ro`.
- Limiares de definição vêm de `ops.parametros`; nunca escritos direto em SQL ou código.
- Toda taxa e todo efeito saem com IC e n. Abaixo do n mínimo: `amostra_suficiente = false`.
- Nunca imprimir conteúdo de conversa em log, teste ou relatório. Só agregados.
- Nenhum segredo no repositório. Credenciais só em `.env` (ignorado pelo git).

## Ambiente
- Windows 10; Docker roda **dentro do WSL**: `wsl -d Ubuntu-22.04 -- bash -lc "cd '/mnt/c/Users/VINICIUS/Desktop/Meus agentes/case_acaso' && docker compose up"`.
- Python local para scripts: `.venv/` (duckdb, pyarrow, pandas, statsmodels, scikit-learn). Rodar com `PYTHONUTF8=1`.
- Máquina com pouca memória: `SET memory_limit='2GB'` no DuckDB; nada de carregar o WildChat inteiro em pandas.
- Dados: `data/bruto/wildchat_brasil.parquet` (snapshot versionado); `data/raw/` (3,4 GB, fora do git).

## Convenções
- Identificadores de banco e API em português, como no design. Código e comentários em português.
- Python: funções puras para regras, tipagem, pytest. TypeScript: modo estrito, zod, vitest.
- Commits pequenos por task, mensagem `tipo(milestone): descrição [T-nnn]`.
- O repositório é **público** em github.com/ViniciusSouzadata/case-acaso desde 16/11/2026; só o histórico limpo vai para lá, e nada mais é publicado sem pedido do Vinícius.
