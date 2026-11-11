# MCP CODESYS + Claude Code: configuração e diagnóstico

Versões observadas no projeto: CODESYS 3.5.22.40, MCP Server 1.1.0.0. O bridge precisa rodar **na mesma máquina** e com a mesma instalação/add-on do IDE.

Referências oficiais:
- https://content.helpme-codesys.com/en/CODESYS%20Development%20System%20MCP%20Server/_idemcp_cmd_configure_mcp_client.html
- https://content.helpme-codesys.com/en/CODESYS%20Development%20System%20MCP%20Server/_idemcp_cmd_enable_mcp_server.html
- https://www.codesys.com/ecosystem/release-lifecycle/releases-updates/development-system-mcp-server/
- https://support.microsoft.com/pt-br/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions

## Checklist rápido

1. Projeto aberto no CODESYS e ponte do mesmo add-on instalado.
2. Ferramentas > Gestor de licenças: PDE/MCP habilitada **nesta máquina**.
3. Ferramentas > Ativar o servidor MCP: ligado; somente uma instância.
4. Ferramentas > Configurar o cliente MCP: caminho exato do bridge.
5. Claude Code no **Windows nativo**, mesma máquina, escopo local e repositório raiz.
6. `claude mcp list` e `/mcp` confirmam conexão, não apenas registro.

Use o caminho exibido em **Ferramentas > Configurar o cliente MCP** (ou liste com `.\tools\diagnose-windows.ps1`). Tabela completa de sintomas: [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md#j-problemas-do-mcp).

~~~powershell
claude mcp add --scope local --transport stdio codesys-ide -- "CAMINHO_REAL_DO_BRIDGE"
claude mcp list
claude mcp get codesys-ide
~~~

## Problemas conhecidos

| Sintoma | Diagnóstico / próxima etapa |
| --- | --- |
| `claude` não reconhecido | Instalar Claude Code no Windows e reiniciar o terminal/VS Code para atualizar PATH |
| `É impossível iniciar o servidor MCP. Ative sua licença` | Licença não ativa/compatível na workstation atual |
| `CONNECTION_CLOSED` | Erro genérico: verificar licença, servidor desligado, caminho desatualizado e logs; não assumir causa |
| Gateway verde, PLC cinza | Gateway funcional, destino Control Win pode não estar iniciado/selecionado; independente do MCP |
| MCP registrado mas desconectado | Registro local não prova que servidor CODESYS esteja ativo |
| Versão nova do add-on | Bridge muda de caminho: atualizar a entrada Claude |

## Histórico confirmado em OUTRO computador (exemplo histórico, não regra)

A conexão falhou com `CONNECTION_CLOSED`. O log de depuração apontou:

~~~text
Could not load file or assembly 'ModelContextProtocol.Core.dll'
Uma política de Controle de Aplicativo bloqueou este arquivo.
0x800711C7
~~~

Um evento CodeIntegrity 3077 identificou a DLL como bloqueada; `Get-AuthenticodeSignature` retornou `NotSigned`. O Smart App Control estava ativo naquele Windows. **Isso não prova que o notebook atual tenha o mesmo problema.**

Se falhar, gere log local:

~~~powershell
claude --debug-file "$env:TEMP\claude-codesys-mcp.log"
~~~

Dentro do Claude, use `/mcp` e tente conectar. Em outro terminal:

~~~powershell
Select-String -Path "$env:TEMP\claude-codesys-mcp.log" -Pattern "codesys-ide|CodesysMCPBridge|Fatal error|CONNECTION_CLOSED|800711C7" | Select-Object -Last 25
~~~

Confira também Segurança do Windows > Controle de aplicativos e do navegador > Controle Inteligente de Aplicativos e Visualizador de Eventos > Microsoft > Windows > CodeIntegrity > Operational. Não publique logs sem revisar credenciais.

**Não desative antivírus, firewall ou controles de execução sem diagnosticar.** Smart App Control não possui exceção por DLL; prefira atualização assinada do fabricante, suporte ou ambiente isolado quando necessário.

## Limitações funcionais

O MCP oficial 1.1.0.0 permite consultar a árvore e documentação, criar/editar **somente Structured Text** (objetos gráficos são só leitura) e obter diagnósticos de compilação. Isso **não implica geração automática de redes Ladder gráficas** nem de telas HMI. Para Ladder, validar importação CODESYS XML / PLCopen XML ou API de automação com evidência de compilação e execução.

MCP é **integração com o editor**. OPC UA/WebSocket é **integração com o CLP e a HMI**. Uma não substitui a outra.
