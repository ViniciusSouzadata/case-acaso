# BDR-06 — Fuso horário
**Atende:** C-13, C-30

## Contexto
O timestamp vem em UTC. "Semana", "manhã" e "fim de semana" só fazem sentido no horário do usuário.

## Opções consideradas
- UTC para tudo.
- **America/Sao_Paulo como fuso do país, com fuso por estado onde o dado informa.**

## Escolha
Segunda opção. Semana e período do dia são calculados no fuso local; UTC fica como sensibilidade.

## Consequências
- A taxa oficial não muda com UTC, mas 44 usuários mudam de semana de coorte.
- No incidente §4.2, a semana calculada no fuso do banco (UTC) é um dos defeitos listados; a correção usa o fuso do país.
- Outros países: cada país teria o próprio fuso; a comparação entre países fica como evolução (ver arquitetura).

## Como defender
- **Por quê:** o cliente pensa na semana dele; uma conversa às 22h de domingo em São Paulo é segunda em UTC.
- **O que descartei:** UTC por simplicidade; troca só 44 usuários de semana, mas erra a leitura de "manhã" e "fim de semana".
- **O que mudaria minha decisão:** dados de países com vários fusos sem informação de região (aí o erro é maior e precisa ser declarado).
- **O que faria diferente:** validar o fuso por estado com uma amostra de perguntas que citam horário.
