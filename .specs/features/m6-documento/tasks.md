# Tasks — M6 Documento

Texto e decisões são escritos pelo **planejador com o Vinícius**; o executor só faz o que é mecânico (diagramas, exportação, README técnico).
```
T-601 (contínua) ─┐
T-602 ────────────┼─► T-604 ─► T-605 ─► T-606 (gate)
T-603 ────────────┘
```

## [ ] T-601 — ADRs e BDRs com "Como defender" (planejador, ao longo da execução)
- **What:** Um arquivo por decisão em `docs/decisoes/` (lista completa no spec.md do M6): Contexto · Opções consideradas · Escolha · Consequências · Como defender. Cada um com o número que sustenta a escolha (ex.: IP + UA completo gera +21% de usuários).
- **Where:** `docs/decisoes/`
- **Depends on:** números do M1 e do M2
- **Reuses:** STATE.md (log de decisões), design.md de cada milestone
- **Done when:** 10 BDRs + 10 ADRs; nenhum com mais de uma página
- **Tests:** revisão: cada decisão cita o C-nn que atende
- **Gate:** Toda decisão do projeto está registrada e defendível
- **Reqs:** REQ-602

## [ ] T-602 — Arquitetura AWS, custo e diagramas (planejador redige; executor gera os diagramas)
- **What:** Diagrama do fluxo bruto → tela (Mermaid, exportado em PNG) e diagrama da implantação AWS; tabela de componentes com o porquê e o custo mensal estimado (preços conferidos na página oficial de cada serviço, com data e link); descrição do deploy; seção de outros países.
- **Where:** `docs/arquitetura/`
- **Depends on:** gate do M3
- **Reuses:** spec M6 — REQ-604, REQ-605; design M3 — Multi-país
- **Done when:** diagramas renderizam; cada preço tem fonte e data
- **Tests:** conferência manual dos preços
- **Gate:** Arquitetura dimensionada ao tamanho real, com custo
- **Reqs:** REQ-604, REQ-605

## [x] T-603 — README final (executor)
- **What:** README completo: pré-requisitos, um comando, o que cada serviço faz e quanto demora, endereços das telas, `make test`, FULL_REFRESH, estrutura de pastas, solução de problemas (porta ocupada, Docker no WSL), licença do dataset.
- **Where:** `README.md`
- **Depends on:** gates de M1..M4
- **Reuses:** READMEs parciais das tasks
- **Done when:** uma pessoa segue o README num clone novo sem ajuda
- **Tests:** execução literal dos passos em pasta limpa
- **Gate:** Avaliador sobe o projeto sozinho
- **Reqs:** REQ-603

## [ ] T-604 — Documento de entrega (planejador + Vinícius)
- **What:** `docs/entrega.md` com as 12 seções do spec, ≤ 8 páginas, cada seção citando os C-nn; 3 achados e decisões; premissas com o número recalculado; riscos e decisões a escalar; sugestões; parágrafo de uso de IA com as horas de `docs/horas.md`.
- **Where:** `docs/entrega.md`, `docs/horas.md`
- **Depends on:** gate do M2, T-505, T-601, T-602
- **Reuses:** `resultado.*`, `docs/figuras/`
- **Done when:** todas as seções escritas; Vinícius leu e concorda com cada frase
- **Tests:** contagem de páginas; verificação de que todo número do texto existe na base
- **Gate:** Documento curto, completo e verdadeiro
- **Reqs:** REQ-601, REQ-606, REQ-607, REQ-608

## [ ] T-605 — Exportação e pacote (executor)
- **What:** Exportar `docs/entrega.md` para PDF; gerar o zip do repositório sem `data/raw`, `data/interim`, `.venv`, `node_modules`, `.env` (com `data/bruto/` incluído); conferir tamanho para envio.
- **Where:** `dist/`
- **Depends on:** T-604, T-603
- **Reuses:** —
- **Done when:** zip descompactado em pasta limpa sobe com um comando
- **Tests:** execução real a partir do zip
- **Gate:** O que será enviado foi testado como o avaliador vai receber
- **Reqs:** REQ-603

## [ ] T-606 — Matriz de exigências fechada (planejador)
- **What:** Preencher "Evidência" e "Status" das 42 linhas de `CASE-REQUIREMENTS.md`.
- **Where:** `.specs/project/CASE-REQUIREMENTS.md`
- **Depends on:** T-605
- **Reuses:** —
- **Done when:** 42 linhas com evidência apontando arquivo, tela ou seção
- **Tests:** revisor independente confere 10 linhas por amostragem
- **Gate:** **Gate de saída do M6** → Auditoria
- **Reqs:** REQ-609
