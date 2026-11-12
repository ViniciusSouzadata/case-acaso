# Proposta dos 3 achados — ponto de controle 1 (planejador, 12/11 00h30)

Para revisão do Vinícius de manhã. Depois de aprovada, a Sessão A transfere para `seeds/achados.yaml` e o documento.
Fonte dos números: relatórios da Sessão A (STATE, `docs/robustez_recusa.md`, `docs/validacao_llm.md`, `resultado.*` versão 1.1.0).

## Achado 1 — Recusa na primeira conversa é o único comportamento do assistente ligado a menos retorno
**Evidência.** Entre 2.372 novos usuários, 132 (5,6%) receberam uma recusa na primeira resposta. Desses, 9,8% voltaram em 7 dias, contra 24,7% dos demais. Comparando pessoas de perfil parecido, a diferença é de 16,4 pontos a menos (de 11,5 a 21,4). É o único fator do assistente que se mantém depois da correção para muitos testes.
**Por que confiar:** o número quase não muda com as quatro definições de usuário e sessão (de −14,4 a −16,4), nem com um aquecimento maior (−16,3). As recusas estão espalhadas (132 recusas em 131 IPs, então não é um usuário só) e a direção se repete nos 5 temas com recusas suficientes. Com o classificador antigo, de palavras-chave, o efeito parecia zero (−3,3). Ele errava 7 em cada 10 recusas marcadas, e isso diluía a diferença.
**Decisão que sustenta:** tratar a taxa de recusa como indicador de saúde do assistente, ao lado da retenção. Revisar quais pedidos estão sendo recusados sem necessidade. Testar de forma controlada (metade dos usuários com cada versão) uma recusa que ofereça uma alternativa útil, antes de mudar para todos.
**Limite:** é comparação, não experimento. A recusa pode ser sinal de um pedido que o produto não atende, e não a causa da saída. Com 132 casos, não deu para montar um grupo de comparação equilibrado (segundo método: não comparável). Para explicar a diferença, um fator escondido precisaria estar fortemente ligado às duas coisas (E-value 5,3). A recusa foi marcada por IA conferida contra 200 rótulos manuais: acerta 81% das que marca e encontra 86% das reais. Esse tipo de erro tende a diminuir a diferença, não a criar.

## Achado 2 — Trocar de modelo ou mudar o formato da resposta não mostrou efeito no retorno
**Evidência.** GPT-4 contra GPT-3.5, entre perfis parecidos: −2,9 pontos (de −8,0 a +2,2). Pelo segundo método, −6,1 (de −12,7 a +0,4). Tamanho da resposta e resposta em outro idioma também não se distinguem de zero. O resultado se repete nas quatro definições.
**Decisão que sustenta:** não esperar ganho de retenção de uma troca de modelo. Se a troca acontecer por custo ou qualidade, medir com teste controlado.
**Limite:** com esta base, só é possível enxergar diferenças a partir de cerca de 5 pontos. Efeitos menores podem existir.

## Achado 3 — Quedas semanais isoladas enganam: a maior era efeito do início da coleta
**Evidência.** A maior queda da série (semana de 01/05/2023: −17,1 pontos, p = 0,013) desaparece quando o início da coleta é tratado com mais folga. Contra as quatro semanas seguintes, a diferença é de −7,7 (p = 0,13), porque as semanas de comparação incluíam usuários antigos contados como novos. Na semana de 20/11/2023, quando chegou um novo modelo, a queda de 4,9 pontos ficou dentro da variação normal (p = 0,43), e quase toda veio de as pessoas voltarem menos, não de mudança no público. Nas 33 semanas testadas, só 1 passou do limite, o que é perto do que o acaso produz.
**Decisão que sustenta:** o alerta do dashboard só dispara quando a queda passa da variação normal, ignora as semanas do início da coleta e mostra quantas semanas passariam por acaso. É a mesma lição do incidente: conferir a definição antes de alarmar.
**Limite:** semanas têm de 18 a 197 usuários, então só quedas grandes são detectáveis.

## Fica fora dos achados (vai para "sinais descritivos" e para a Tela 2)
- Engajamento: 4 ou mais mensagens na primeira sessão dão 32,9% de retorno, contra 17,2% com 1 mensagem. Isso descreve, não prova causa, porque acontece junto com o interesse.
- Tema (IA, concordância moderada, kappa 0,48): conversa pessoal/conselho −8,2 (não passa na correção para muitos testes). Só descritivo.

## Perguntas para o Vinícius
1. Concorda em trocar o achado de engajamento pelo de modelo?
2. A decisão do achado 1 (recusa com alternativa + teste controlado) soa como algo que você defenderia para um cliente?
