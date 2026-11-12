# BDR-01 — Quem é "um usuário"
**Atende:** C-09, C-16, C-13

## Contexto
O WildChat não tem ID de usuário. Só há `hashed_ip` e o `user-agent` (navegador e sistema). Retenção mede "a mesma pessoa voltou", então a regra de identidade muda a resposta.

## Opções consideradas
| Chave | Usuários no Brasil | Problema |
|---|---:|---|
| Só `hashed_ip` | 2.385 | junta gente diferente atrás do mesmo IP (rede compartilhada, celular) |
| IP + user-agent completo | 2.895 (+21%) | cada atualização de navegador vira "pessoa nova" |
| **IP + família do user-agent** (sistema + navegador, sem versão) | 2.530 (+6%) | meio-termo; ainda junta quem usa o mesmo tipo de aparelho no mesmo IP |

## Escolha
**IP + família do user-agent.** A regra mora num lugar só (a carga) e tem versão (`ops.parametros`, 1.0.0).

## Consequências
- Taxa de retorno em 7 dias: 23,86% (oficial), 23,94% (só IP), 25,14% (IP + UA completo). A leitura quase não depende da chave (variação de ±1,3 ponto).
- O painel mostra as três linhas na tela de sensibilidade.

## Como defender
- **Por quê:** o dataset não permite certeza; o meio-termo erra menos nos dois sentidos e o resultado foi testado nas três chaves.
- **O que descartei:** IP + UA completo, porque fabrica usuários novos (é exatamente o defeito do incidente do §4.2).
- **O que mudaria minha decisão:** um ID de conta real (login) ou evidência de que a maioria dos IPs é de rede compartilhada.
- **O que faria diferente:** com mais tempo, cruzaria com idioma e fuso do navegador para separar pessoas atrás do mesmo IP.
