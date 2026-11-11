# Discovery — resumo dos fatos (10/11/2026)

Fonte: `01_extract_output.txt`, `02_profile_output.txt`, `03_followup_output.txt` (só agregados).
Obs.: o 02 calculou "início" com o último turno (usuário não tem timestamp); números de retenção válidos são os do 03.

## Tamanho e período
- **11.621 conversas** Brasil (1,39% da base; 14º país). Só 5 conversas têm turno BR com país top-level ≠ Brasil → filtro por conversa não perde nada relevante.
- Período: **08/04/2023 → 29/04/2024** (~55 semanas).
- Identidade: **2.385 IPs**; 2.895 IP+UA (+21%); 2.530 IP+família de UA (+6%).
- **Base pequena:** ~45 a 100 usuários novos por semana. Retorno 7d global (IP, sessão 30 min): **577 / 2.385 = 24,2%**.
  - Erro de uma taxa semanal (n≈50, p≈0,25) ≈ ±12 p.p. → **variação semana a semana é quase toda ruído**. Coorte mensal ou janela móvel de 4 semanas.
  - Efeito mínimo detectável de um fator binário 50/50 ≈ 5 p.p.; 15/85 ≈ 7 p.p.

## Estrutura do dado (corrige premissas)
- **Usuário não tem timestamp**; só o assistente (hora em que a resposta chegou). Início da conversa = timestamp da 1ª resposta. **Latência não é mensurável** (retirar do plano).
- `hashed_ip`/`header` existem só nos turnos de usuário.
- Duração da conversa: mediana 0 min (1 turno), p90 21 min, p99 5,8 h.
- **56% das conversas têm 1 turno.**

## Concentração e anomalias
- **Top 1% dos IPs = 41% das conversas; top 10 IPs = 32,5%.** Mediana: 1 conversa por IP.
- **Um único IP = 1.557 conversas (13,4%)**, Piauí, 35 UAs, 129 dias ativos → explica o Piauí em 3º lugar entre os estados. Usuário intenso, IP compartilhado ou automação — tratar à parte.
- Outros IPs pesados: 648, 319, 249, 207 conversas.
- Semanas anômalas: 09/10/2023 (46 conversas, 9 novos, 0 voltaram) e 05/02/2024 (39) → provável indisponibilidade do serviço.
- 27 hashes repetidos (93 conversas com conteúdo idêntico).

## Modelo = tempo (confusão estrutural)
| Período | GPT-4 disponível? | % GPT-4 |
|---|---|---|
| abr–jun/2023 | sim (gpt-4-0314) | 13–16% |
| **jul–out/2023** | **não** | **0%** |
| nov/2023 | volta (gpt-4-1106-preview) | 15% |
| dez/2023–abr/2024 | vira padrão | 75–94% |
→ "Quem escolhe GPT-4 é mais engajado" só pode ser testado onde havia escolha (abr–jun e nov/2023). No resto, o modelo é decidido pela oferta, não pelo usuário → efeito de modelo tem de ser estimado **dentro do período** (efeito fixo de período) e o mudança de dez/2023 é um **experimento natural**.

## Idioma, estado, dispositivo
- Português 76%, inglês 16%, espanhol 1,4%; "Latin", "Sotho", "Finnish" = erro de detecção em texto curto (qualidade).
- SP 2.589, RJ 1.769, PI 1.581 (efeito do IP pesado), MG 991, MA 767. 51 sem estado.
- Android/Chrome 3.825, Windows/Chrome 3.739, Windows/Edge 1.957 → **celular ≈ 35%**.

## Qualidade
- `toxic` = 0% (tóxicas removidas pelos autores). `redacted` = 0,48%.
- 273 conversas com input vazio; 175 com IP mudando no meio da conversa.
- Recusa (heurística na 1ª resposta) ≈ 6,3% — a validar.

## Sessão
- 58% dos intervalos entre conversas consecutivas do mesmo IP são < 30 min; 65% < 60 min; 87% < 24 h → conversas se agrupam em sessões; o limiar muda quem "voltou". Sensibilidade obrigatória (30 min × 60 min × "dia seguinte").

## Incidente §4.2
- Os números do incidente (1.210 novos/semana) **não existem no WildChat Brasil** (~50–70/semana): é cenário de referência. Não dá para "reproduzir"; dá para mostrar o mecanismo (IP+UA fragmenta: 2.895 × 2.385 usuários = +21%) e os UAs por IP (mediana 1, p99 5, máx 35).
- Curiosidade real: coorte por IP cai de 30% (06/11) para 17% (20/11/2023), mas com n≈50–64 o IC é de ±10 p.p.
