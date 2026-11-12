# ADR-02 — Texto de conversa fora da base e papéis de acesso
**Atende:** C-12, C-10

## Contexto
O dataset tem o texto das conversas. O Postgres alimenta a API e a tela.

## Opções consideradas
- Guardar o texto no Postgres "para consulta".
- **Guardar só atributos derivados (tamanho, idioma, recusa, tema) e deixar o texto no arquivo bruto.**

## Escolha
Segunda opção. A carga lê o arquivo, calcula os atributos e grava só eles. Dois papéis: `loader_rw` (carga e transformação) e `app_ro` (só leitura em `mart.*` e `resultado.*`; sem acesso a `stg` e a `ops.parametros`).

## Consequências
- Se o Postgres ou a API vazarem, não há conversa nem `hashed_ip` na tela ou na resposta.
- Tema e recusa precisam ser calculados antes de gravar: o texto só passa pelo classificador (regras ou LLM), e o resultado volta como rótulo.
- Testes verificam que `app_ro` não consegue ler `stg` e `ops.parametros`.

## Como defender
- **Por quê:** privilégio mínimo; o app não precisa do que não vai mostrar.
- **O que descartei:** guardar texto "criptografado"; adiciona chave para gerenciar e nenhuma pergunta do cliente exige o texto.
- **O que mudaria minha decisão:** uma tela de "explorar conversas" pedida pelo cliente, com revisão de privacidade.
- **Ponto de atenção:** a leitura de conversa para classificação com LLM manda texto truncado a um serviço externo; por isso o ADR-09 separa dataset público de dado de cliente.
