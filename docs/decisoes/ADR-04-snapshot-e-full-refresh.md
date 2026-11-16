# ADR-04 — Snapshot versionado e `FULL_REFRESH`
**Atende:** C-14, C-08

## Contexto
O WildChat-1M tem 3,4 GB; o avaliador precisa subir o projeto do zero, sem baixar nada pesado nem ter credencial.

## Opções consideradas
- Baixar o WildChat completo em toda subida.
- **Snapshot do recorte Brasil dentro do repositório (`data/bruto/wildchat_brasil.parquet`) e um modo opcional de reextração completa (`FULL_REFRESH=1`).**

## Escolha
Segunda opção. O snapshot tem 11.621 conversas do Brasil, é verificado por checksum na subida, e é a base de todos os números do documento. `FULL_REFRESH` refaz o recorte a partir do dataset completo.

## Consequências
- Sobe em cerca de 2 minutos na primeira vez e 30 segundos nas seguintes.
- O repositório é público no GitHub (github.com/ViniciusSouzadata/case-acaso) desde 16/11/2026, por decisão do Vinícius para a entrega; o zip da entrega leva o snapshot, mas não `data/raw`.
- Número novo só aparece se o snapshot ou a definição mudarem, e a reconciliação mostra a diferença.

## Como defender
- **Por quê:** reprodutibilidade; o mesmo arquivo dá o mesmo número em qualquer máquina.
- **O que descartei:** download na subida (lento, depende de rede e de conta no Hugging Face).
- **O que mudaria minha decisão:** dado atualizado todo dia; aí o recorte virá de um bucket e o snapshot só serve de teste.
- **Limite conhecido:** `FULL_REFRESH` precisa rodar fora do compose (o diretório de dados é montado só para leitura).
