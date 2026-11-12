# Checklist do gate de saída do M4 (T-406)

Feito localmente (sem Docker), com o banco da Sessão A (`app_ro`, somente leitura):

- [x] `tsc --noEmit` limpo; vitest sem banco: 149 passam (17 de fumaça pulam sem `DATABASE_URL`).
- [x] Fumaça da API contra o banco real: 14/14 rotas validadas pelo esquema do contrato, sem dado sensível.
- [x] Fumaça das telas (`tests/fumaca-telas.test.tsx`): Tela 1, 2 e 3 renderizam com dados reais; o "i" abre o glossário com a definição e o SQL; o HTML não traz IP, user-agent nem hash.
- [x] Textos de `pt.json` contra o REQ-409: nenhum "regressão", "propensão" ou "p-valor" (teste em `componentes.test.tsx`); termos técnicos só no detalhe recolhível.
- [x] Conferência visual no navegador das 3 telas (1280 px).
- [ ] Largura de celular: conferir as 3 telas a ~390 px (precisa do app no ar).

Fica para UMA rodada, depois que a Sessão A fechar a T-209 (não subir build em paralelo):

- [ ] `docker compose up` do zero: 2 telas Must com dados reais.
- [ ] `make test` no compose (inclui o serviço `app-testes`).
- [ ] Build da imagem do app + `/api/saude` no compose (prova pendente da T-301).
