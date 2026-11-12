# BDR-08 — Fatores em três grupos: assistente, perfil e engajamento
**Atende:** C-05, C-06, C-17, C-24

## Contexto
O cliente quer saber o que faz voltar, separando "o que o assistente faz" (que ele pode mudar) de "quem é o usuário" (que ele não controla) e de "como a pessoa usou" (que acontece junto com o retorno).

## Opções consideradas
- Uma lista única de fatores.
- **Três grupos:** assistente (recusa, tamanho da resposta, modelo, idioma divergente), perfil (tema, idioma, dispositivo, período do dia, fim de semana, tamanho da pergunta, região, era do modelo) e engajamento (turnos e conversas na 1ª sessão).

## Escolha
Três grupos. Engajamento fica **fora** do modelo ajustado e é mostrado só como descrição.

## Consequências
- Engajamento: 4 ou mais mensagens na 1ª sessão volta 32,9% contra 17,2% de quem teve 1 (diferença de 15,6 pontos). É um sinal, não uma causa: quem se interessa conversa mais e volta mais.
- Idioma divergente só conta para perguntas com mais de 30 caracteres: nas curtas, 61% apareciam como "divergentes" por erro de detecção.
- Resposta curta (até 300 caracteres) tem retorno mais baixo no bruto (19,5%); no modelo ajustado o efeito encolhe e o intervalo cruza zero.

## Como defender
- **Por quê:** misturar os grupos faz o cliente achar que dá para "aumentar turnos" como alavanca.
- **O que descartei:** colocar turnos no modelo; seria controlar por algo que vem depois da primeira experiência.
- **O que mudaria minha decisão:** um experimento controlado (teste A/B), que é o que provaria causa.
- **Limite:** o modelo ajustado tem 25 parâmetros; por isso o tema entra com 4 níveis e a região com 3.
