# BDR-02 — O que é sessão e o que é "voltar em 7 dias"
**Atende:** C-16, C-13

## Contexto
"Voltou em 7 dias" depende de duas escolhas: quando duas conversas são a mesma visita (sessão) e quanto tempo vale a janela.

## Opções consideradas
- Sessão: intervalo máximo de 30 min (**escolhida**) × 60 min.
- Retorno: nova sessão que começa em até 7 dias (168 h, limite incluído) depois do **início** da 1ª sessão (**escolhida**) × "voltou em outro dia".

## Escolha
Sessão = conversas com intervalo ≤ 30 min, medido do **fim** da anterior ao **início** da seguinte (58% dos intervalos entre conversas ficam abaixo de 30 min). Retorno = nova sessão com início em até 168 h do início da 1ª.

## Consequências
| Variação | Taxa |
|---|---:|
| Oficial (30 min, 7 dias) | 23,86% (566 de 2.372) |
| Sessão de 60 min | 21,54% |
| "Voltou em outro dia" | 16,86% |

Cerca de 166 dos 566 retornos oficiais são outra sessão **no mesmo dia**. A manchete honesta é "entre 17% e 24%, conforme o que o cliente chama de voltar". O painel mostra as duas leituras.

## Como defender
- **Por quê:** segue a lógica da referência do case (mais de 1 h no mesmo dia já conta como retorno) e vem de um número do dado (58% dos intervalos).
- **O que descartei:** só "outro dia" como oficial, porque muda a pergunta do cliente; ele entra como sensibilidade.
- **O que mudaria minha decisão:** o cliente dizer que voltar é só em outro dia.
- **Prova de que não muda em silêncio:** testes de borda (exatamente 168 h e exatamente 30 min) e teste de versão da definição. Trocar `<=` por `<` não era pego até eu acrescentar a borda.
