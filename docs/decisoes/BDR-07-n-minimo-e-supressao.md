# BDR-07 — Amostra mínima e o que o painel faz com ela
**Atende:** C-28, C-06, C-12

## Contexto
A base é pequena: cerca de 45 a 100 usuários novos por semana, 2.372 elegíveis no total. Taxa e efeito de grupo pequeno enganam.

## Opções consideradas
- Mostrar tudo.
- **Toda taxa e todo efeito saem com intervalo de confiança e n; abaixo do n mínimo, o painel mostra "amostra insuficiente" em vez do número.**

## Escolha
Segunda opção. O n mínimo é parâmetro (`ops.parametros`). No modelo, níveis com menos de 30 usuários são juntados à referência (dispositivo "outro" com 11, região "não informado" com 14); só o resultado bruto aparece, com a explicação.

## Consequências
- Intervalo de 95% da taxa global: 22,19% a 25,62%. Efeito mínimo detectável com 80% de poder: **4,9 pontos** (grupos 50/50) e **6,87 pontos** (15/85). O painel diz isso: efeito menor que isso não dá para enxergar.
- Isso também protege privacidade: grupo minúsculo não é mostrado.

## Como defender
- **Por quê:** "17% contra 24%" com 30 pessoas é ruído, e o cliente não técnico lê a barra, não o n.
- **O que descartei:** esconder o intervalo; o cliente precisa ver quanto o número pode variar.
- **O que mudaria minha decisão:** uma base maior; o limiar de n cairia.
- **Frase pronta:** "não se distingue de zero" é um resultado, não uma falha: diz o que os dados permitem afirmar.
