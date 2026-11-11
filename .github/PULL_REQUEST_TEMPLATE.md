## O que muda e por quê
<!-- Descreva em 2–4 linhas. Linke a issue: Fixes #123 -->

## Tipo
- [ ] Correção
- [ ] Melhoria
- [ ] Documentação
- [ ] Testes
- [ ] Outro:

## Checklist
- [ ] Rodei `tools\run-tests.ps1` (e `-E2E` se mexi na interface) e passou
- [ ] Se mudei o Ladder: regenerei o XML (`tools/gen_ld_xml.py`) e as imagens (`tools/render_ladder.py`); um único escritor por saída
- [ ] Não enfraqueci nenhum teste (se a expectativa mudou, expliquei acima)
- [ ] A interface continua **só solicitando**; o selo DEMO / SIMULADO continua visível
- [ ] Sem senhas, tickets, `references/`, `.opt` ou caminhos pessoais
- [ ] Links dos documentos funcionam; índice `docs/README.md` atualizado se movi arquivos
- [ ] Diferenciei **comprovado**, **simulado** e **hipótese** nos textos
- [ ] Registrei no `CHANGELOG.md` se a mudança é relevante

## Como testei
<!-- Comandos executados e resultado; para a interface, uma captura ajuda. -->
