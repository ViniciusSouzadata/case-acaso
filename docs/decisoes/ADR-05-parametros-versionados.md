# ADR-05 — Parâmetros de definição versionados no banco
**Atende:** C-16, C-13, C-34

## Contexto
Os limiares que definem o indicador (gap de sessão, janela de retorno, burn-in, limiares de tráfego anômalo, n mínimo) não podem ficar espalhados em SQL e código, nem mudar sem registro.

## Opções consideradas
- Constantes no código.
- **Tabela `ops.parametros`, com versão da definição (`versao_definicao`, hoje 1.0.0), lida pelo SQL e pela análise.**

## Escolha
Segunda opção. Cada execução grava a versão usada em `resultado.meta` (e a versão da análise).

## Consequências
- Trocar um limiar em um lugar muda o cálculo em todos; o teste de versão compara os valores do banco com um arquivo de referência.
- A sensibilidade (60 min, sem burn-in, UTC, com anômalos) usa a mesma função com argumentos, então não existe uma segunda definição escondida.
- Limiar de diagnóstico que não define o indicador (por exemplo, "semana com queda forte") fica no código, documentado.

## Como defender
- **Por quê:** "o número mudou" passa a ter resposta: a versão mudou, ou o dado mudou.
- **O que descartei:** configuração por arquivo `.env` (mistura segredo com definição de negócio).
- **O que mudaria minha decisão:** vários clientes com definições diferentes (aí seria um parâmetro por cliente).
