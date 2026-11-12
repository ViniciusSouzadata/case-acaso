<!-- RASCUNHO da Sessão A (T-505): só as seções do §4 (sustentação e incidente). Revisão do planejador e do Vinícius antes de entrar no documento final (T-604).
     Os números do incidente do case (1.210, 1.188, 2.034 novos) vêm do enunciado; os do WildChat vêm de docs/incidente/evidencia.md. -->

# §4 — Sustentação e investigação de falhas

## 4.1 Como eu saberia que um número está errado

### O que registramos em cada camada
| Camada | O que fica registrado | Para que serve |
|---|---|---|
| **Carga** | um registro por execução em `ops.lote_carga` (arquivo de origem, checksum, versão da definição, linhas lidas, gravadas e rejeitadas, início, fim, status); cada linha rejeitada em `ops.rejeitado` com o motivo | saber de qual arquivo e de qual versão da regra veio o número, e se a carga foi parcial |
| **Base analítica** | versão da definição em `ops.parametros` e em `resultado.meta`; reconciliação bruto × base em `ops.reconciliacao` (9 métricas) | dizer "o número mudou porque a regra mudou" ou "porque o dado mudou" |
| **Backend** | um log em JSON por requisição, com `request_id`, rota, tempo (`Server-Timing`) e a versão dos dados; erro devolve o `request_id` | achar a consulta exata que gerou o que a tela mostrou |
| **Tela** | `request_id` visível no erro; rodapé com data da carga e versão da definição | o usuário consegue citar o que viu |

**Caminho para investigar um número errado:** tela (`request_id` e rodapé) → log da requisição → consulta SQL → tabela `mart` → lote em `ops.lote_carga` → arquivo bruto. Em nenhum ponto aparece texto de conversa, IP ou user-agent.

### Como perceber a divergência antes do cliente
- **Reconciliação automática a cada carga:** o loader refaz 9 métricas direto do arquivo bruto (conversas, IPs, usuários, elegíveis, retornos, semanas maduras e semanas divergentes) e compara com a base. Hoje: diferença 0 nas 9.
- **Regras de alerta** (descritas; a reconciliação já roda, o envio do alerta fica como próximo passo):
  1. diferença acima da tolerância em qualquer métrica reconciliada;
  2. "novos usuários" da semana mais de 3 desvios-padrão fora da média das 8 semanas anteriores;
  3. salto no número de user-agents por IP (o sinal exato do incidente).

### Testes que impedem a definição de mudar em silêncio
- **Base sintética de resposta conhecida:** casos escritos à mão (retorno em 6 d 23 h conta, 7 d + 1 min não; intervalo de exatamente 30 min é a mesma sessão; troca de versão do navegador é a mesma pessoa; 1 IP com 12 user-agents é tráfego anômalo; conversa vazia não conta). A resposta esperada fica em `tests/esperado.py`.
- **Versão da definição:** os parâmetros do banco são comparados com um arquivo de referência; mudar um sem subir a versão derruba o teste.
- **Contrato da API:** campo a mais, a menos ou de tipo errado falha.
- **Um comando:** `make test` (ou `docker compose run --rm loader ...`). Provei que os testes pegam: gap de sessão de 30 para 60 minutos sem subir a versão derrubou o teste de versão; trocar `<=` por `<` na janela de 7 dias só foi pego depois que acrescentei os testes de borda.

### Caminho até produção
1. **Ambientes:** local (compose) → homologação → produção, com a mesma imagem e configuração por variável.
2. **Migrações:** arquivos SQL numerados e aplicados em ordem, com registro em `ops.schema_migrations`. **A reversão de cada migração ainda não está escrita no repositório (migrações só andam para frente hoje); descrever o passo inverso é parte do caminho até produção.**
3. **Deploy:** imagem versionada (a tag é o commit); nunca construir em produção.
4. **Verificação depois do deploy:** `/api/saude` e uma reconciliação; só depois o tráfego entra.
5. **Reversão:** voltar para a imagem anterior; se a migração mudou dados, restaurar pelo backup (ou pelo passo inverso, quando existir). Reconstruir os marts a partir do bruto é seguro porque a carga é idempotente.
6. **CI:** rodar lint e testes antes de aceitar a mudança (workflow descrito; ainda não configurado).

## 4.2 Incidente: a retenção do dashboard caiu de 31% para 18%

### Pergunta 1 — Por onde eu começaria e por quê
Reconciliando as duas fontes **na mesma granularidade** (semana). A tabela do enunciado já aponta o caminho:

| Semana | Novos (dashboard) | Novos (relatório) | Voltaram (dashboard) | Voltaram (relatório) |
|---|---:|---:|---:|---:|
| 06/11 | 1.210 | 1.150 | 375 | 345 |
| 13/11 | 1.188 | 1.131 | 368 | 351 |
| 20/11 | **2.034** | 1.172 | 366 | 352 |

Quem **voltou** fica estável nas duas fontes; quem **chegou** explode só no dashboard (+862, +73,5%). A queda não é de comportamento: é de **contagem de usuários novos**. Em semanas normais as duas fontes já divergiam cerca de 5%, o que indica definições de usuário diferentes desde antes. Com cerca de 1.200 usuários por semana, o intervalo de 95% da taxa é de aproximadamente ±2,6 pontos: 31% para 30% é ruído; 31% para 18% não é.

### Pergunta 2 — Em qual camada está a falha, com que evidência
Na **carga**, na definição de `usuario_id`. O relatório conta por `hashed_ip`; a carga conta por `hashed_ip|user-agent`. O endpoint calcula certo sobre o que recebe, e a tela só exibe.

Há três explicações possíveis para "mais novos, mesmos retornos", e todas apontam para a mesma linha: um IP com user-agent rotativo (robô), um IP compartilhado com muita gente de verdade, ou usuários antigos que atualizaram o navegador. A carga duplicada fica descartada: `ON CONFLICT DO NOTHING` não duplica a conversa, e duplicar conversa não cria usuário.

**Consulta de confirmação** (`docs/incidente/confirmacao.sql`; a mesma lógica roda no arquivo bruto com `scripts/incidente_confirmacao.py`): para cada semana, usuários novos pela chave IP + user-agent, pela chave IP, quantos "novos" caem em IP que já existia e o máximo de user-agents novos por IP.

**Mecanismo mostrado com dado real** (WildChat Brasil, `docs/incidente/evidencia.md`): 2.385 usuários pela chave IP contra **2.895 pela chave IP + user-agent (+21,4%)**, 510 "novos" a mais caindo em IP já visto, e até 35 user-agents diferentes em um único IP. Os números do enunciado (1.210 por semana) não existem neste dado; o que mostro é o mecanismo.

### Pergunta 3 — O trecho que causa o problema e a correção
O trecho: `chave = f"{hashed_ip}|{user-agent}"`. Cada versão de navegador, e cada navegador de um mesmo IP, vira "uma pessoa nova".

Outros defeitos do mesmo endpoint, mesmo sem relação direta com a queda: a "primeira vez" usa o **último** turno da conversa; coortes dos últimos 7 dias não são marcadas como imaturas; `date_trunc('week')` roda no fuso do banco (UTC); `ON CONFLICT DO NOTHING` congela conversa que continua em outro dia; a inserção é linha a linha, sem transação nem registro de lote.

**Correção escrita** em `docs/incidente/correcao/`:
- `carga_corrigida.py`: identidade vinda de **uma regra única** (IP + família do navegador, sem versão), upsert com `ON CONFLICT DO UPDATE`, **um lote em uma transação** e registro do lote.
- `route_corrigida.ts`: usuário vindo de `mart.dim_usuario`, início da primeira sessão (não o último turno), semana no fuso do país, coortes imaturas marcadas.
Os dois arquivos têm um comentário `DEFEITO:` em cada linha corrigida, e passam em `py_compile` e `tsc --noEmit --strict`.

### Pergunta 4 — O que mais fazer além do código e como evitar que volte
1. **Reprocessar o histórico** com a regra corrigida (a carga é idempotente) e **versionar** a mudança de definição.
2. **Alinhar a definição** com o relatório do time de dados: a causa organizacional são duas definições de usuário e nenhuma reconciliação.
3. **Reconciliação automática e alerta** (seção 4.1): salto de "novos" e de user-agents por IP.
4. **Teste de regressão** (`tests/test_regressao_incidente.py`): na base sintética, a troca de versão do navegador não cria usuário novo e o IP com 12 user-agents não entra nos "novos"; o teste também mostra que, com a chave do incidente, a mesma verificação falha.
5. **Registro pós-incidente:** causa, impacto, correção e o que mudou no processo; as semanas anteriores tinham cerca de 5% de viés que também foi corrigido.

### Pergunta 5 — O que eu diria à gerente de produto

**Durante (hoje):**
> "A queda de 31% para 18% é quase certamente de **medição**, não de comportamento: o número de pessoas que voltaram não mudou, só o de pessoas que chegaram. Por favor, **não tome decisão em cima do 18%**. Estou confirmando a causa e volto a falar com você até [horário]."

**Depois:**
> "A causa foi a forma como o dashboard identifica uma pessoa nova: uma troca de navegador estava contando como usuário novo. Com a regra corrigida, a retenção da semana de 20/11 é [X%], com margem de [±Y pontos]. As semanas anteriores tinham um erro pequeno (cerca de 5%), que também foi corrigido. A contagem agora é conferida automaticamente com o relatório do time de dados, e há um teste que impede esse erro de voltar. Os números que você já mostrou para outras pessoas: [lista], com a versão corrigida."

<!-- Os campos [horário], [X%] e [Y pontos] dependem de rodar a regra corrigida nos dados reais do cliente; no case não existem. -->
