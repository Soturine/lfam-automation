# CP2 - POC Ladder (parcial) - 2026-11-11

Caminho comprovado para criar LD: **PLCopen XML + Scripting API** (o MCP 1.1.0.0 não cria LD).
- `tools/codesys_scripts/probe_export.py`: abre CÓPIA do projeto em instância headless (`tools/run-codesys-script.ps1`) e exporta
  `PLC_PRG` -> confirmado que PLC_PRG original é **LD** vazio (só `leftPowerRail`/`rightPowerRail`).
- `codesys/exports/POC_PLC_PRG.xml`: 1 rede LD real (contato BT_TESTE, contato negado FALHA_TESTE, bobina EST_TESTE).
- `tools/codesys_scripts/poc_build.py`: importa o XML na cópia, `app.build()` -> **0 mensagens/0 erros**; salva `work/LFAM_POC.project`.
- Observação: `import_xml(..., Replace)` não substituiu (gerou `PLC_PRG_1`); o script remove o PLC_PRG vazio antes.

NÃO comprovado ainda: execução no Control Win. `login()` headless (--noUI) travou (provável diálogo de gateway/dispositivo).
Passo manual: abrir `work/LFAM_POC.project` no IDE, ativar/selecionar o gateway local e rodar
`tools/codesys_scripts/poc_online_in_ide.py` (Tools > Scripting > Execute Script File) ou logar (Alt+F8) e start.
O projeto original `LFAM_Automacao.project` NÃO foi modificado (trabalho só em cópias em `work/`, ignorado pelo Git).

## Atualização: causa raiz do bloqueio de login (observada)
- Fix 1: o gateway/dispositivo ativo fica no `.opt` do usuário; a cópia `work/LFAM_POC` recebeu cópia local dele.
- Com isso o `login()` headless deixou de ser cego: o log de prompts (`system.log_prompt_details`) mostrou
  `Prompt_ActivateUserManagement_New`: o dispositivo **exige gerenciamento de usuários** e o Control Win local não tem usuário.
  O diálogo ficava invisível em `--noUI`, daí o travamento.
- Responder "Não" via `system.prompt_answers` faz o login falhar ("Operação cancelada pelo usuário"); não há bypass por script.
- Pendente (decisão do dono): criar o admin do runtime local no IDE (Online > Login, senha só local) ou desligar a exigência
  de gerenciamento de usuários na CÓPIA `LFAM_POC.project` (Configurações do projeto). Execução online ainda NÃO observada.
- `tools/codesys_scripts/poc_online.py`: login com `OnlineChangeOption.Try` e `delete_foreign_apps=False`.
