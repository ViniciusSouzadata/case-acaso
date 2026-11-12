# ADR-06 — Next.js com rotas de API (em vez de um backend separado)
**Atende:** C-29, C-03

## Contexto
O case pede frontend, backend e base analítica. O volume é baixo e a equipe do projeto é uma pessoa.

## Opções consideradas
- Frontend + backend separados (por exemplo, API em outro serviço).
- **Um app Next.js (TypeScript estrito) com rotas de API que leem só `mart.*` e `resultado.*`.**

## Escolha
Segunda opção, com contratos validados por zod (entrada e saída), SQL parametrizado, envelope de resposta e log JSON por requisição com `request_id`.

## Consequências
- Um só deploy e uma só imagem; menos peças para operar.
- O contrato da API é testado (campo a mais, a menos ou de tipo errado falha).
- Se a API precisar ser usada por outros clientes ou escalar de forma independente, separar vira uma etapa clara: as rotas já estão isoladas em `lib/consultas`.

## Como defender
- **Por quê:** menos partes, mesmo isolamento de dados (papel `app_ro`).
- **O que descartei:** serviço separado por ora; seria arquitetura para um problema que não existe.
- **O que mudaria minha decisão:** vários consumidores da API, ou carga que exija escalar o backend sozinho.
- **Ponto fraco declarado:** eu tenho mais experiência em Python/SQL que em Next.js; por isso a análise está em Python e o app só lê o que ela produz.
