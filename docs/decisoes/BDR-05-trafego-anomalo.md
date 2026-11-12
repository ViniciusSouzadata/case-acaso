# BDR-05 — Tráfego anômalo
**Atende:** C-19, C-13

## Contexto
Alguns IPs concentram volume incompatível com uma pessoa: o IP mais ativo tem 1.557 conversas (13,4% da base) e há IPs com até 35 user-agents diferentes.

## Opções consideradas
- Manter todos.
- **Marcar como anômalo o IP com 200 conversas ou mais, ou 10 user-agents distintos ou mais, e tirá-lo do modelo principal.**
- Remover só pelo volume.

## Escolha
Segunda opção. O limiar está em `ops.parametros` (`limiar_conversas_ip`, `limiar_uas_ip`), não no código. O texto completo do user-agent entra na contagem, não a família.

## Consequências
- 11 usuários de 7 IPs saem da análise principal. Com eles incluídos a taxa seria 24,08% (sensibilidade).
- Todos os usuários de um IP anômalo ficam marcados.
- Há um caso sintético de teste (1 IP com 12 user-agents) que nunca pode virar "12 usuários novos" (T-503).

## Como defender
- **Por quê:** um IP que parece robô ou rede pública enorme distorce o denominador e o efeito de fatores; tirar poucos usuários não muda o número (24,08% × 23,86%).
- **O que descartei:** apagar os dados; eles ficam na base e aparecem na tela de qualidade.
- **O que mudaria minha decisão:** saber que esses IPs são uma escola ou empresa real; aí o certo seria identificar pessoas dentro do IP, não excluir.
- **Limite honesto:** os limiares (200 e 10) são de bom senso, não estimados; por isso o resultado com e sem eles está registrado.
