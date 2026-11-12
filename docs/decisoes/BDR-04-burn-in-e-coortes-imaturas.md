# BDR-04 — Burn-in e coortes imaturas
**Atende:** C-13, C-16

## Contexto
A base é uma janela no tempo (abr/2023 a abr/2024). No começo, "novo" inclui gente que já usava antes da janela; no fim, quem chegou nos últimos dias ainda não teve 7 dias para voltar.

## Opções consideradas
- Usar tudo.
- **Excluir as 2 primeiras semanas (burn-in) e quem não tem janela completa de 7 dias (imaturos).**

## Escolha
Segunda opção, com os limiares guardados em `ops.parametros` (14 dias de burn-in, 168 horas de janela).

## Consequências
- Dos usuários com uso, 2.372 são elegíveis. Ficam de fora 64 por burn-in, 51 por imaturidade e 11 por tráfego anômalo (BDR-05).
- Sem o burn-in a taxa vai de 23,86% para 24,01%: a escolha é conservadora e quase não muda o número.
- No painel, coortes imaturas aparecem marcadas ("ainda sem janela completa") em vez de uma queda falsa.

## Como defender
- **Por quê:** sem isso, a taxa das últimas semanas cai só porque falta tempo de observação (censura à direita), e a das primeiras mistura gente antiga (censura à esquerda).
- **O que descartei:** incluir tudo e "corrigir depois"; a queda de fim de período viraria achado falso.
- **O que mudaria minha decisão:** uma base mais longa, onde 2 semanas pesam pouco.
- **Mesma lição do incidente §4.2:** o código de referência não marca coorte imatura; a correção marca.
