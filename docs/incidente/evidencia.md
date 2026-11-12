# Incidente §4.2: evidência do mecanismo no dado real (WildChat Brasil)

Gerado por `scripts/incidente_confirmacao.py` sobre o snapshot; só agregados.

## Resumo
- Usuários pela chave `hashed_ip`: **2.385**
- Usuários pela chave `hashed_ip|user-agent` (a do código de referência): **2.895** (+21,4%)
- Dos 2.895 "novos" pela chave IP+UA, **510** caem em um IP que já tinha aparecido antes (mesma pessoa ou mesmo lugar, outro navegador)
- Máximo de user-agents diferentes em um único IP: **35**

## Por semana (semana no fuso de São Paulo, início da conversa)
| Semana | Novos por IP | Novos por IP+UA | Dos novos IP+UA, em IP já visto | Máx. UAs novos num IP |
|---|---:|---:|---:|---:|
| 03/04/2023 | 9 | 10 | 1 | 2 |
| 10/04/2023 | 33 | 41 | 8 | 2 |
| 17/04/2023 | 26 | 31 | 5 | 2 |
| 24/04/2023 | 63 | 75 | 12 | 3 |
| 01/05/2023 | 80 | 92 | 12 | 4 |
| 08/05/2023 | 83 | 100 | 17 | 5 |
| 15/05/2023 | 76 | 88 | 12 | 3 |
| 22/05/2023 | 84 | 91 | 7 | 2 |
| 29/05/2023 | 88 | 99 | 11 | 2 |
| 05/06/2023 | 56 | 73 | 17 | 3 |
| 12/06/2023 | 62 | 77 | 15 | 2 |
| 19/06/2023 | 40 | 42 | 2 | 1 |
| 26/06/2023 | 41 | 47 | 6 | 3 |
| 03/07/2023 | 40 | 48 | 8 | 2 |
| 10/07/2023 | 52 | 63 | 11 | 2 |
| 17/07/2023 | 34 | 36 | 2 | 1 |
| 24/07/2023 | 25 | 29 | 4 | 2 |
| 31/07/2023 | 42 | 47 | 5 | 1 |
| 07/08/2023 | 41 | 52 | 11 | 2 |
| 14/08/2023 | 37 | 47 | 10 | 2 |
| 21/08/2023 | 31 | 40 | 9 | 1 |
| 28/08/2023 | 36 | 42 | 6 | 2 |
| 04/09/2023 | 36 | 48 | 12 | 2 |
| 11/09/2023 | 24 | 35 | 11 | 2 |
| 18/09/2023 | 20 | 25 | 5 | 1 |
| 25/09/2023 | 32 | 43 | 11 | 2 |
| 02/10/2023 | 33 | 43 | 10 | 2 |
| 09/10/2023 | 9 | 9 | 0 | 1 |
| 16/10/2023 | 24 | 29 | 5 | 2 |
| 23/10/2023 | 45 | 51 | 6 | 2 |
| 30/10/2023 | 47 | 58 | 11 | 3 |
| 06/11/2023 | 45 | 59 | 14 | 3 |
| 13/11/2023 | 51 | 62 | 11 | 3 |
| 20/11/2023 | 64 | 72 | 8 | 3 |
| 27/11/2023 | 62 | 72 | 10 | 2 |
| 04/12/2023 | 43 | 53 | 10 | 2 |
| 11/12/2023 | 23 | 27 | 4 | 2 |
| 18/12/2023 | 15 | 21 | 6 | 2 |
| 25/12/2023 | 13 | 22 | 9 | 4 |
| 01/01/2024 | 8 | 15 | 7 | 5 |
| 08/01/2024 | 25 | 37 | 12 | 3 |
| 15/01/2024 | 21 | 37 | 16 | 3 |
| 22/01/2024 | 20 | 28 | 8 | 2 |
| 29/01/2024 | 15 | 19 | 4 | 2 |
| 05/02/2024 | 10 | 13 | 3 | 2 |
| 12/02/2024 | 27 | 35 | 8 | 3 |
| 19/02/2024 | 58 | 75 | 17 | 3 |
| 26/02/2024 | 63 | 74 | 11 | 3 |
| 04/03/2024 | 42 | 47 | 5 | 1 |
| 11/03/2024 | 63 | 75 | 12 | 2 |
| 18/03/2024 | 99 | 113 | 14 | 2 |
| 25/03/2024 | 53 | 65 | 12 | 2 |
| 01/04/2024 | 59 | 74 | 15 | 3 |
| 08/04/2024 | 49 | 56 | 7 | 2 |
| 15/04/2024 | 53 | 62 | 9 | 2 |
| 22/04/2024 | 49 | 61 | 12 | 3 |
| 29/04/2024 | 6 | 10 | 4 | 2 |

## Como ler
A chave com user-agent conta como "novo" quem só trocou de navegador ou de versão, e conta cada navegador de um mesmo IP como uma pessoa. Isso infla o denominador da retenção (novos), enquanto o numerador (quem voltou) quase não muda: é o padrão do incidente. Os números do case (1.210 novos por semana) não existem neste dado; aqui se mostra o mecanismo.
