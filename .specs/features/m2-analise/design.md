# M2 — Design da análise

## Entrada e população
`mart.fct_primeira_experiencia` com `elegivel = true` (maduro, fora do burn-in, sem tráfego anômalo). Desfecho: `voltou_7d`.

## Passos (pacote `analise/`, executado pelo `loader` depois dos marts)
1. **Descritivo** → `resultado.eda_*` e figuras em `docs/figuras/`.
2. **Bruto**: por fator/nível, diferença de proporções contra a referência (nível mais frequente), IC de Newcombe.
3. **Ajustado**: `statsmodels` Logit; `cov_type='cluster'` por `hashed_ip`; efeito marginal médio por nível (diferença média de probabilidade prevista), IC pelo método delta.
4. **Propensão** (recusa, idioma divergente, modelo nas eras com escolha): Logit do tratamento em covariáveis pré-resposta (perfil + era + tamanho da pergunta); pesos estabilizados truncados em p1/p99; balanço por diferença padronizada (meta < 0,1); efeito = diferença ponderada; IC por bootstrap de 1.000 reamostragens por IP, semente fixa.
5. **E-value** a partir da razão de riscos ajustada.
6. **Comparações múltiplas**: Benjamini-Hochberg a 5% sobre os p-valores ajustados.
7. **Semana**: decomposição de Kitagawa — Δ = Σ(Δpeso × taxa média) [mix] + Σ(peso médio × Δtaxa) [taxa].
8. **Sensibilidade**: repete o passo 3 nas definições alternativas.
9. **Validação**: compara seed de tema e `recusa_1` com `seeds/validacao_manual.csv`.

## Por que estes métodos (resumo para "Como defender")
- Logística + efeito marginal: resposta sim/não; o resultado sai em pontos percentuais, que o cliente entende.
- Erro agrupado por IP: usuários do mesmo IP não são independentes.
- Bruto × ajustado lado a lado: a diferença entre os dois **é** a seleção que o case pede para separar.
- Propensão com balanço: mostra, numa tabela, que os grupos comparados ficaram parecidos.
- E-value: diz quão forte um fator invisível teria de ser para anular o efeito — honestidade sobre o que não se prova.
- Engajamento fora do ajuste: turnos acontecem depois da resposta; ajustar por eles esconderia o efeito do assistente.

## Contrato das tabelas de resultado (congelado — M3/M4 dependem dele)

### resultado.meta
`versao_analise, versao_definicao, executado_em, n_elegiveis, n_retornos, taxa_global, ic_inf, ic_sup, efeito_minimo_detectavel_pp`

### resultado.efeito_fator
| coluna | tipo | nota |
|---|---|---|
| fator, nivel, referencia | text | |
| grupo | text | `assistente` \| `perfil` \| `engajamento` |
| n_nivel, n_referencia | int | |
| taxa_nivel, taxa_referencia | numeric | 0–1 |
| efeito_bruto_pp, bruto_ic_inf, bruto_ic_sup | numeric | pontos percentuais |
| efeito_ajustado_pp, ajustado_ic_inf, ajustado_ic_sup | numeric | nulo para `engajamento` |
| p_valor, significativo_fdr | numeric, bool | |
| e_value | numeric | só `assistente` |
| metodo | text | `logit_ame` \| `ipw` |
| amostra_suficiente | bool | n_nivel ≥ n_minimo |
| leitura | text | frase simples gerada por regra, ex.: "Quem recebeu recusa voltou 6 p.p. menos (entre 1 e 11)" |
| ordem | int | por \|efeito_ajustado_pp\| decrescente |

### resultado.balanco_propensao
`tratamento, covariavel, dp_antes, dp_depois`

### resultado.decomposicao_semana
`semana, segmento, peso_base, peso_semana, taxa_base, taxa_semana, efeito_mix_pp, efeito_taxa_pp`
### resultado.decomposicao_resumo
`semana, base_descricao, n_base, n_semana, taxa_base, taxa_semana, delta_pp, mix_pp, taxa_pp, p_valor, conclusao`

### resultado.sensibilidade_efeito
`definicao, fator, nivel, efeito_ajustado_pp, ic_inf, ic_sup, mesmo_sinal`

### resultado.validacao_classificador
`classificador, n, acuracia, kappa, detalhe_json, versao_prompt, modelo`

### resultado.achado
`ordem, titulo, evidencia, decisao, limite`

### resultado.problema_qualidade
`problema, contagem, percentual, tratamento`

## Tema (REQ-251)
- Taxonomia v1 (ajustável após a validação): estudo/dever de casa; programação/TI; escrita e tradução; trabalho/negócios; criação/ficção e roleplay; informação geral/curiosidade; conversa pessoal/conselho; outros/indefinido.
- Script `classificador/tema_bedrock.py`: lê a 1ª pergunta (truncada em ~1.000 caracteres) do snapshot, chama Bedrock (Claude Haiku; reserva Amazon Nova), saída JSON validada, grava `seeds/tema_conversa.csv` com `modelo` e `versao_prompt`. Roda fora do compose, uma vez; credencial em `.env`.
- Texto enviado ao Bedrock: só a 1ª pergunta, já anonimizada pelos autores do dataset; nada é gravado além do rótulo.

## Riscos
- Poucos eventos em níveis raros → agrupar; mostrar "amostra insuficiente".
- Balanço não atingido → reportar o efeito como "não comparável" em vez de forçar.
- Vinícius precisa explicar cada passo → `docs/adr` com "Como defender" + M7.
