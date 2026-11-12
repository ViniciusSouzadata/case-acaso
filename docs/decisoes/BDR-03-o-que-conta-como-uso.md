# BDR-03 — O que conta como uso
**Atende:** C-19, C-13

## Contexto
Algumas conversas não são uso de verdade: pergunta vazia, conversa sem resposta do assistente.

## Opções consideradas
- Contar toda conversa carregada.
- **Contar só conversas com pelo menos uma mensagem de usuário não vazia e uma resposta do assistente.**

## Escolha
Segunda opção. A conversa sem resposta do assistente é rejeitada na carga e registrada com motivo; a que só tem pergunta vazia entra na base, mas não conta como uso e não vira usuário nem retorno.

## Consequências
- No dado real: 141 conversas com a 1ª pergunta vazia e 76 que não contam como uso. Nenhuma linha rejeitada na carga (11.621 lidas, 11.621 gravadas).
- Contar as vazias muda pouco (23,69% contra 23,86%), e o painel registra a diferença como sensibilidade.
- Correção de número: o "273 conversas vazias" do discovery contava qualquer turno vazio; os números corretos são 141 e 76.

## Como defender
- **Por quê:** pergunta vazia não é ação de pessoa e não mostra interesse; contar inflaria retornos com "visitas" sem pedido.
- **O que mudaria minha decisão:** saber que a tela do produto grava conversa vazia quando a pessoa abre o app (aí seria sinal de abertura, outra métrica).
- **O que faria diferente:** medir "abriu o app sem perguntar" separadamente, se o cliente tiver esse dado.
