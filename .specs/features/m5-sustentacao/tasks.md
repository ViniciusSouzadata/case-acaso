# Tasks — M5 Sustentação

Pode começar após o gate do M1. Não depende de M2/M3/M4, exceto T-503.
```
T-501 ─► T-502 ─┐
T-504 ──────────┼─► T-505 (gate)
T-503 ──────────┘
```

## [x] T-501 — Consulta de confirmação do incidente, rodável no bruto
- **What:** `docs/incidente/confirmacao.sql` (versão Postgres, como o case usa) e `scripts/incidente_confirmacao.py` (mesma lógica em DuckDB sobre o snapshot): por semana, usuários novos pela chave `hashed_ip|user-agent` × pela chave `hashed_ip`, quantos "novos" caem em IP já visto, e o máximo de user-agents novos por IP. Saída só com agregados, gravada em `docs/incidente/evidencia.md` (mostra o mecanismo com dado real: IP + UA gera mais "usuários" que IP).
- **Where:** `docs/incidente/`, `scripts/`
- **Depends on:** T-110
- **Reuses:** docs/discovery/incidente-4.2-raciocinio.md; scripts/discovery/02_profile_brazil.py (consultas do incidente)
- **Done when:** o script roda no snapshot e reproduz os números do discovery (2.385 × 2.895 usuários)
- **Tests:** teste de fumaça do script na base sintética (caso E: 1 IP, 12 user-agents)
- **Gate:** A hipótese do incidente tem consulta que roda
- **Reqs:** REQ-512

## [x] T-502 — Correção escrita do código de referência
- **What:** `docs/incidente/correcao/`: `carga_corrigida.py` (identidade vinda de uma regra única, upsert `ON CONFLICT DO UPDATE`, transação por lote, registro de lote) e `route_corrigida.ts` (início da conversa em vez do último turno, semana no fuso do país, coortes imaturas marcadas, mesma definição de usuário). Cada alteração com comentário de uma linha dizendo o defeito que resolve. É código de documentação: precisa ser sintaticamente válido, não precisa rodar no compose.
- **Where:** `docs/incidente/correcao/`
- **Depends on:** T-501
- **Reuses:** código do §4.2 do case (transcrito em docs/incidente/referencia/)
- **Done when:** `python -m py_compile` e `tsc --noEmit` passam nos dois arquivos
- **Tests:** os dois comandos acima
- **Gate:** Correção concreta, não descrição
- **Reqs:** REQ-513

## [ ] T-503 — Teste de regressão do incidente na suíte
- **What:** `tests/test_regressao_incidente.py`: na base sintética, o IP com 12 user-agents (caso E) e a troca de versão do navegador (caso D) não podem inflar "novos" pela chave oficial; o teste mostra que pela chave `hashed_ip|user-agent` inflaria.
- **Where:** `tests/`
- **Depends on:** T-109
- **Reuses:** T-105
- **Done when:** teste verde; trocar a chave oficial pela do incidente faz o teste falhar
- **Tests:** o próprio + a falha provocada, registrada no relatório
- **Gate:** O incidente não volta sem um teste quebrar
- **Reqs:** REQ-516

## [ ] T-504 — CI (Could)
- **What:** `.github/workflows/ci.yml`: sobe o compose, roda `make test` (Python + TypeScript) e lint.
- **Where:** `.github/workflows/`
- **Depends on:** T-109, T-305
- **Reuses:** Makefile
- **Done when:** workflow válido (`actionlint` ou revisão de sintaxe); execução real só se o repositório privado estiver no GitHub
- **Tests:** validação de sintaxe
- **Gate:** Caminho até produção começa por um portão automático
- **Reqs:** REQ-505

## [ ] T-505 — Texto do §4 (planejador + Vinícius)
- **What:** Escrever em `docs/entrega.md` as seções de sustentação e do incidente (5 respostas na ordem do case; tabela de registros por camada; regras de alerta; caminho até produção; mensagem para a gerente de produto). **Escrito pelo planejador, não pelo executor**, usando a evidência das T-501..T-503.
- **Where:** `docs/entrega.md`
- **Depends on:** T-501, T-502, T-503
- **Reuses:** docs/discovery/incidente-4.2-raciocinio.md
- **Done when:** C-32 a C-39 com evidência em CASE-REQUIREMENTS.md
- **Tests:** leitura a frio por revisor
- **Gate:** **Gate de saída do M5**
- **Reqs:** REQ-501, REQ-502, REQ-503, REQ-504, REQ-510..REQ-515
