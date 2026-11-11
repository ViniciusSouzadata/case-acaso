# Rotulagem das 200 conversas (tarefa do Vinícius, ~1 h)

**Para quê:** conferir se o computador acertou o *tema* e a *recusa*. É a resposta a "como você conferiu o que a IA fez?" — vira um número (acerto e kappa) no documento.

**Arquivo:** `seeds/validacao_manual_em_branco.csv` (só na sua máquina; não vai para o git porque tem texto de conversa). Abra no Excel ou LibreOffice (separador: ponto e vírgula). Cada linha mostra a **1ª pergunta** e a **1ª resposta** do assistente (cortadas em 600 caracteres). Você **não** vê o que o computador respondeu — de propósito.

## Preencha duas colunas
1. **`tema_vinicius`** — escreva **exatamente** um destes (copie e cole):
   - `estudo/dever de casa`
   - `programação/TI`
   - `escrita e tradução`
   - `trabalho/negócios`
   - `criação/ficção e roleplay`
   - `informação geral/curiosidade`
   - `conversa pessoal/conselho`
   - `outros/indefinido`
   
   Regra prática: escolha o assunto **principal da pergunta**. Se ficar em dúvida entre dois, escolha o que um leitor apressado diria. Pergunta sem sentido, só "oi" solto sem contexto de pedido ou impossível de entender: `outros/indefinido` (mas "oi, tudo bem?" é `conversa pessoal/conselho`).
2. **`recusa_vinicius`** — `sim` se a **resposta** do assistente **recusou** o pedido (disse que não podia/não ia atender, mesmo que tenha dado alguma explicação ou alternativa); `não` caso contrário. Resposta que atende o pedido com um aviso no meio **não** é recusa.

## Quando terminar
Salve como **`seeds/validacao_manual_preenchida.csv`** (CSV, separador ponto e vírgula, UTF-8) e avise. O resto é automático: um comando tira o texto e guarda só os rótulos (`seeds/validacao_manual.csv`), e outro compara com o computador.

Não precisa ser perfeito: o que importa é a sua leitura honesta. Se uma linha for impossível de rotular, escolha `outros/indefinido` e `não`.
