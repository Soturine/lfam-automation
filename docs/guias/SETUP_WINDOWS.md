# Instalação no Windows

O passo a passo completo (conta CODESYS Store, instalação, Control Win, administrador do CLP virtual, licença,
MCP e Claude Code) está em **[INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md)**.

Resumo rápido para quem já tem tudo instalado e só quer retomar o trabalho:

~~~powershell
cd <pasta-onde-clonou>\lfam-automation
git status
git pull --ff-only            # salve e feche o CODESYS antes; nunca use reset --hard
.\tools\diagnose-windows.ps1 # descobre CODESYS, Control Win, bridge MCP e ferramentas automaticamente
~~~

- O projeto é `codesys/LFAM_Automacao_Ladder.project`. Não mova o arquivo com o CODESYS aberto.
- Scripts de automação trabalham em **cópias** em `work/` (ignorada pelo Git), nunca no projeto original.
- Problemas de MCP: [MCP_TROUBLESHOOTING.md](MCP_TROUBLESHOOTING.md).
