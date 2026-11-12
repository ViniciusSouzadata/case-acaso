# ADR-08 — Arquitetura na AWS e custo
**Atende:** C-11, C-29

## Contexto
O case pede que toda a infraestrutura do dashboard e o LLM rodem na AWS, e que a entrega local descreva a implantação.

## Opções consideradas
Componentes e custos estão em `docs/arquitetura/arquitetura.md` (preços conferidos na página oficial de cada serviço, com data e link). Resumo da escolha:
- **Banco:** Postgres gerenciado (RDS), porque é o mesmo motor do desenvolvimento.
- **App:** container do Next.js em serviço de container gerenciado.
- **LLM:** Amazon Bedrock (ver ADR-09).
- **Carga:** tarefa agendada que roda o mesmo container do loader.

## Escolha
Mesmos containers do compose, trocando só a configuração (conexão, credencial por papel IAM, região).

## Consequências
- O compose sobe sem credencial AWS; o seed do classificador vem versionado.
- O custo mensal e a projeção de LLM estão separados (`docs/custo_llm.md`).

## Como defender
- **Por quê:** o caminho local→AWS é por configuração, o que reduz risco na entrega.
- **O que descartei:** serviços de orquestração mais pesados; o volume não justifica.
- **O que eu não fiz:** implantar de verdade na AWS. É um desenho, e o documento diz isso; AWS gerenciada em produção é um gap meu declarado.
- **O que mudaria minha decisão:** exigência de rede privada, auditoria ou várias regiões.
