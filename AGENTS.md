# AGENTS.md — guia para agentes de IA (e para quem chega agora)

Projeto **educacional** de Automação Industrial: Ladder real (CODESYS Control Win) + backend FastAPI + SCADA React + planta simulada para uma extrusora LFAM. Visão geral: [docs/entender/COMO_FUNCIONA.md](docs/entender/COMO_FUNCIONA.md) · índice: [docs/README.md](docs/README.md) · contribuição: [CONTRIBUTING.md](CONTRIBUTING.md).

## Mapa do repositório
| Caminho | O que é |
|---|---|
| `codesys/generator/` | **Fonte do Ladder** (DSL Python → PLCopen XML) + avaliador de referência |
| `codesys/exports/LFAM_PROGRAM.xml` | XML gerado (não editar à mão) |
| `codesys/LFAM_Automacao_Ladder.project` | Projeto CODESYS com o Ladder completo e o OPC UA configurados |
| `backend/` | FastAPI: `engine.py`, `transport.py` (DEMO e OPC UA), `app.py` |
| `scada/web/` | React 18 + TypeScript + Vite; E2E em `e2e/` (Playwright) |
| `simulator/` | Planta física didática |
| `tools/` | Scripts: `setup/start-demo/start-plc/run-tests.ps1`, geradores, ensaios, `check_links.py` |
| `tests/` | pytest (Ladder por rede, simulador, backend, OPC UA de teste, segurança do avaliador) |
| `docs/` | `entender/`, `guias/`, `academico/`, `projeto/`, `evidence/`, `media/` |

## Comandos
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1          # instala backend e SCADA
powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1      # pytest + build do SCADA (-E2E inclui Playwright)
.\.venv\Scripts\python.exe tools\gen_ld_xml.py                      # regera o XML do Ladder
.\.venv\Scripts\python.exe tools\render_ladder.py                   # regera docs/entender/LADDER.md e as imagens
.\.venv\Scripts\python.exe tools\check_links.py                     # confere os links dos .md
powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1     # SCADA em DEMO (-Stop encerra)
```

## Regras inegociáveis
1. **O Ladder decide.** A interface e o backend só *solicitam*; o backend escreve **apenas entradas** da lista branca (`WRITABLE` em `backend/transport.py`), nunca saídas do programa. "Confirmado" só aparece quando o estado volta do CLP.
2. **Emergência não é software.** Nunca apresente a interface como parada de emergência; mantenha o aviso.
3. **DEMO ≠ CLP.** O selo **DEMO / SIMULADO** é obrigatório; dados simulados nunca podem parecer medições do CLP. Não classifique como "feito" o que só existe em DEMO.
4. **Ladder só pelo gerador.** Mude `codesys/generator/`, regere o XML e as imagens. **Um escritor por saída.** PID **sem contatos antes** (roda todo ciclo; bloqueio no `RESET` e no portão do SSR). Presets de `TON` como `inVariable` (o importador perde literais dentro do pino).
5. **Não enfraqueça testes.** Se a expectativa mudou, justifique. Compilar não é executar: separe *gerado*, *importado*, *compilado*, *executado*, *comunicando*, *testado*.
6. **Segurança de credenciais.** Senhas só em variáveis de ambiente da sessão; nunca em arquivo, log, commit ou issue. Não desative nem contorne a autenticação do dispositivo; não adicione acesso anônimo ao OPC UA.
7. **Não versionar:** `references/` (materiais do grupo), ZIPs, licenças, tickets, `.opt`, `work/` (cópias e artefatos locais), credenciais.
8. **Não sobrescreva o projeto aberto no IDE.** Scripts do CODESYS trabalham em cópias dentro de `work/` e só depois o resultado é promovido a `codesys/LFAM_Automacao_Ladder.project`.

## Ao mexer em documentação
Escreva em português claro para quem chega de fora; diferencie **comprovado / compilado / simulado / hipótese**; mantenha o índice [docs/README.md](docs/README.md) e rode `check_links.py`. Mudanças relevantes entram no [CHANGELOG](CHANGELOG.md).

## Preferências do mantenedor para Git
Commits em partes coerentes (nem um por arquivo, nem um gigante), mensagens curtas com tipo (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), com a **identidade Git local do mantenedor** e **sem** trailers `Co-Authored-By` de IA. Push em `main` apenas depois de validar (testes passando); sem force push.

## Gates antes de concluir uma tarefa
`tools\run-tests.ps1` passa · `check_links.py` sem links quebrados · se mexeu no Ladder: XML e imagens regerados · se mexeu na interface: E2E passa · nenhum segredo no diff.
