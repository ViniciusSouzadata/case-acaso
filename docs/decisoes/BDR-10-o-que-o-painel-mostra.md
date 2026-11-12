# BDR-10 — O que o painel mostra e o que nunca mostra
**Atende:** C-12, C-07, C-28

## Contexto
A base tem `hashed_ip`, user-agent e texto de conversa. O cliente quer números, não pessoas.

## Opções consideradas
- Mostrar exemplos de conversa para "dar contexto".
- **Mostrar só agregados, com intervalo e n, e nunca dado pessoal.**

## Escolha
Segunda opção, em três camadas:
1. **O texto da conversa não entra no Postgres.** Só o rótulo (tema, recusa) entra; o texto fica no arquivo bruto.
2. **A aplicação lê só `mart.*` e `resultado.*`**, com um papel somente leitura (`app_ro`). A carga usa outro papel (`loader_rw`).
3. **Nunca aparecem na tela, na API, em log ou em teste:** texto de conversa, `hashed_ip`, user-agent.

## Consequências
- A tela de qualidade mostra contagens ("141 perguntas vazias"), não linhas.
- Cada número tem definição e fonte (dicionário de indicadores) e cada efeito tem intervalo.
- O `request_id` aparece no erro, para investigar sem expor dados.

## Como defender
- **Por quê:** o valor para o cliente está em padrões, e o risco de mostrar IP ou texto é maior que qualquer ganho.
- **O que descartei:** exemplos de conversa; 56 conversas vêm marcadas como `redacted` pelos autores do dataset, sinal de que havia dado pessoal no texto.
- **O que mudaria minha decisão:** consentimento explícito e revisão jurídica, com dado de cliente.
- **Verificação:** testes que procuram campos proibidos nas respostas da API.
