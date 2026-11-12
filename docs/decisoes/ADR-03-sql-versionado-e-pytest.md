# ADR-03 — SQL versionado e pytest (dbt como evolução)
**Atende:** C-34, C-14

## Contexto
O §4.1 pede testes que impeçam a definição de um indicador mudar sem ninguém perceber.

## Opções consideradas
- dbt com testes de dados.
- **Migrações SQL numeradas + pytest com base sintética de resposta conhecida.**

## Escolha
Migrações em `sql/migrations/NNN_*.sql`, aplicadas em ordem e registradas em `ops.schema_migrations`; testes em pytest. dbt fica citado como evolução.

## Consequências
- Há uma base sintética pequena com casos de borda escritos à mão (retorno em 6 d 23 h conta; 7 d + 1 min não; troca de versão do navegador é a mesma pessoa; 1 IP com 12 user-agents é anômalo). A resposta esperada de cada caso está em `tests/esperado.py`.
- Os parâmetros da definição têm versão (1.0.0); mudar um sem subir a versão derruba um teste.
- Provas de falha feitas de propósito: gap de sessão de 30 para 60 sem subir a versão → teste falha; janela de retorno alterada → o caso A falha; trocar `<=` por `<` só foi pego depois que acrescentei os testes de borda.

## Como defender
- **Por quê:** SQL, pytest e migrações são o que eu uso e consigo explicar linha a linha; o risco era escolher uma ferramenta que eu não domino.
- **O que descartei:** dbt. É a evolução natural (testes declarativos, linhagem), mas eu não o usei em produção, e o case é pequeno.
- **O que mudaria minha decisão:** muitos modelos de transformação ou um time de dados que já use dbt.
- **O que faria diferente:** migrar os testes de definição para dbt, mantendo a mesma base sintética como fonte da verdade.
