# Como contribuir

Obrigado por querer ajudar! Este é um projeto **educacional** de Automação Industrial; qualquer pessoa do grupo (ou de fora) pode propor correções, melhorias e dúvidas por **Issue** ou **Pull Request (PR)**.

## Antes de começar
- Entenda o projeto em 10 minutos: [docs/entender/COMO_FUNCIONA.md](docs/entender/COMO_FUNCIONA.md). Índice de tudo: [docs/README.md](docs/README.md).
- Dúvida sobre o trabalho ou a arguição? Veja primeiro [PERGUNTAS_E_RESPOSTAS](docs/academico/PERGUNTAS_E_RESPOSTAS.md).

## Quero reportar um problema ou sugerir algo (Issue)
Abra uma [Issue](../../issues/new/choose) escolhendo o modelo: **erro**, **melhoria**, **documentação** ou **pergunta**. Ajuda muito informar: o que você esperava, o que aconteceu, o modo (DEMO ou CLP), a versão do CODESYS e a mensagem exata (em modo CLP, `/api/health` mostra `link_error`).
**Nunca cole senhas, tickets de licença ou caminhos pessoais** em issues.

## Quero corrigir ou adicionar (Pull Request)
1. Faça um *fork* (ou crie uma branch, se tiver acesso): `git checkout -b tipo/descricao-curta` (ex.: `docs/corrige-passo-instalacao`).
2. Prepare o ambiente: `powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1`.
3. Faça a mudança **pequena e focada**; um assunto por PR.
4. Rode os testes: `powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1` (inclui a verificação de links dos documentos; use `-E2E` se mexeu na interface).
5. Abra o PR preenchendo o modelo. Descreva **o quê** e **por quê**.

### Regras que protegem o projeto
- **Ladder:** não edite o XML à mão. A fonte é o gerador em `codesys/generator/`. Depois de mudar redes: `python tools/gen_ld_xml.py` e `python tools/render_ladder.py`, e mantenha **um único escritor por saída** (há teste).
- **Testes:** não enfraqueça um teste para fazê-lo passar. Se a expectativa mudou, explique o motivo no PR.
- **Segurança:** a interface **só solicita**; quem decide é o Ladder. Não escreva em saídas do programa pelo backend, não adicione acesso anônimo ao OPC UA e não grave credenciais em arquivo, log ou Git.
- **Honestidade:** diferencie *comprovado*, *compilado*, *simulado* e *hipótese*. Dados de DEMO nunca podem parecer dados do CLP (o selo **DEMO / SIMULADO** é obrigatório).
- **Não versione:** `references/` (materiais do grupo), ZIPs, licenças e tickets, arquivos `.opt`, credenciais.
- **Documentação:** mantenha os links funcionando; ao mover arquivos, atualize o índice em `docs/README.md`.

### Mensagens de commit
Curtas e no imperativo, com tipo: `feat:`, `fix:`, `docs:`, `test:`, `chore:` (ex.: `fix(ladder): corrige preset do TON de encharque`). Registre mudanças relevantes no [CHANGELOG](CHANGELOG.md).

## Perguntas
Use uma Issue com o modelo **Pergunta**: assim a resposta ajuda quem vier depois.

Ao contribuir você concorda em licenciar sua contribuição sob a [licença MIT](LICENSE) do projeto e em seguir o [Código de Conduta](CODE_OF_CONDUCT.md).
