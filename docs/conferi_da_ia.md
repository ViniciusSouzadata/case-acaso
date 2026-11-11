# O que conferi do que a IA gerou (casos reais do projeto)

Material para o parágrafo de IA do documento e para a entrevista. Cada caso: o que a IA entregou, como foi pego, o que mudou. Só agregados; nada de conversa.

## 1. Efeito marginal médio que não zerava o cenário de referência (T-204)
- **O que a IA gerou:** a função do efeito marginal médio ligava o nível (`x = 1`) para todos, mas não zerava o nível no cenário de comparação: comparava "todos com o nível" contra "como estavam".
- **Como foi pego:** teste de simulação com efeito conhecido e confusão (o perfil `z` empurra a exposição `x` e o retorno). O verdadeiro era +10,1 p.p.; a função estimou +7,0 (IC 6,2 a 7,8), fora do intervalo.
- **Correção:** zerar o nível no cenário de referência (`x0[coluna] = 0`). Depois: estimativa dentro do IC, e o bruto fica claramente enviesado (a confusão o infla), como o teste também exige.
- **Lição:** código estatístico precisa de um teste com resposta conhecida; "converge e dá um número plausível" não prova nada.

## 2. Ruído de detecção de idioma tratado como fator (T-202/T-203)
- **O que apareceu:** o idioma da resposta diferente do da pergunta em 16,8% das conversas, com efeito bruto de −4,6 p.p. no retorno.
- **Como foi pego:** taxa de divergência por faixa de tamanho da pergunta: 61% em até 30 caracteres contra 10% nas mais longas — detecção falha em texto curto.
- **Correção:** o fator só vale para perguntas com mais de 30 caracteres. Resultado: +3,0 p.p. bruto (−3,9 a 10,8) e +1,8 ajustado (−6,2 a 9,9); indistinguível de zero.
- **Lição:** antes de chamar uma variável de "causa", checar se ela mede o que o nome diz.

## 3. Teste por casos deixava passar a mudança de limite (T-109)
- **O que aconteceu:** trocar `<=` por `<` na janela de retorno (exatamente 168 h) e no intervalo de sessão (exatamente 30 min) não derrubava nenhum teste.
- **Correção:** casos de borda (exatamente 168 h; exatamente 30 min). Só então a mudança foi pega.

## 4. Consulta correta, mas lenta (T-110)
- **O que a IA gerou:** CTE de IPs anômalos reexecutada por usuário (subconsulta correlacionada); `mart.calc_retencao` levava ~12 s por chamada.
- **Correção:** materializar a CTE e ligá-la por JOIN: 0,33 s por chamada. Tabela de sensibilidade idêntica antes e depois (diff linha a linha).
