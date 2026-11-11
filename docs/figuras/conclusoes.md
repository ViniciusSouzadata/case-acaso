# Conclusão de cada figura

Cada figura tem uma frase de conclusão; os números saem do cálculo que gerou a figura (`python -m analise eda`).

- `01_volume_semanal.png`: O volume semanal tem mediana de 163 conversas (de 40 a 616, sem as semanas parciais das pontas); semanas com queda forte (menos da metade das vizinhas): 10/04/2023 (159 conversas); 09/10/2023 (46 conversas); 29/01/2024 (62 conversas); 05/02/2024 (40 conversas). Queda de volume pode ser indisponibilidade do serviço ou fim de um pico de interesse; não é lida como mudança de comportamento do usuário.
- `02_concentracao_ip.png`: Há 2.385 IPs distintos; o 1% mais ativo (24 IPs) responde por 41% das conversas e o IP mais ativo sozinho por 13,4%. A mediana é de 1 conversa por IP: IPs de volume anômalo precisam ficar fora do modelo principal.
- `03_retorno_semanal.png`: Entre as 36 semanas maduras com n suficiente, a faixa de incerteza de cada ponto tem em média 22 p.p. de largura: a variação semana a semana é em grande parte ruído. A média móvel de 4 semanas fica entre 14% e 38%.
- `04_turnos.png`: 56% das conversas que contam como uso têm um único turno e 84% têm até três: o engajamento dentro da conversa é curto e vem depois da resposta, por isso entra como sinal de engajamento e não como fator do assistente.
- `05_retorno_por_tema.png`: O tema com maior retorno é 'criação/ficção e roleplay' (31%) e o menor é 'conversa pessoal/conselho' (16%); os intervalos não se sobrepõem.
- `06_idioma.png`: Portuguese responde por 70% das conversas. O idioma da resposta difere do da pergunta em 61% das perguntas de até 30 caracteres contra 10% nas mais longas: em pergunta curta isso é sobretudo erro de detecção, então o fator 'idioma divergente' é restrito a perguntas com mais de 30 caracteres.
