# Instalação e retomada — Windows (LFAM)

Este guia documenta a instalação **no notebook**, sem sobrescrever o projeto existente. O projeto confirmado no GitHub é **`LFAM_Automacao.project` na raiz**, e não em `codesys/`.

## 1. Pré-requisitos

- Windows 64 bits, PowerShell e permissões para instalar software.
- Git e VS Code.
- Claude Code para Windows (CLI nativa, não WSL para o MCP local).
- CODESYS Development System V3.5 SP22 Patch 4 (3.5.22.40).
- CODESYS Control Win V3 x64.
- CODESYS Development System MCP Server 1.1.0.0 (add-on separado).
- Licença PDE / MCP válida **no computador atual**; não presumir que a licença de outro PC foi transferida.
- Python e Node.js LTS somente quando iniciar backend e SCADA.

Instalações oficiais: https://www.codesys.com/ecosystem/services/download/ , https://www.codesys.com/ecosystem/release-lifecycle/releases-updates/development-system-mcp-server/ , https://code.claude.com/docs/en/setup , https://nodejs.org/en/download , https://www.python.org/downloads/windows/ .

## 2. Preparar repositório

~~~powershell
git --version
claude --version
cd "$HOME\Desktop\github\lfam-automation"
git status
git remote -v
~~~

Caso a pasta ainda não exista, clone a URL privada com autenticação GitHub:

~~~powershell
New-Item -ItemType Directory -Force "$HOME\Desktop\github" | Out-Null
cd "$HOME\Desktop\github"
git clone https://github.com/Soturine/lfam-automation.git
cd lfam-automation
~~~

Se o projeto já estiver sendo editado, **salve e feche o CODESYS** antes de atualizar o checkout. Confira as alterações locais com `git status` e preserve as que são suas; depois faça `git pull --ff-only`. Não execute `git reset --hard`.

Configuração de autor, **apenas neste repositório** se necessário:

~~~powershell
git config --local user.name "Soturine"
git config --local user.email "SEU_EMAIL_GIT_CONFIGURADO"
~~~

Use seu e-mail real de commit ou endereço noreply autorizado. Não configure autor global nem adicione Co-Authored-By de IA.

## 3. Abrir e validar o arquivo CODESYS

No CODESYS use Arquivo > Abrir projeto e selecione:

~~~text
C:\Users\<usuario>\Desktop\github\lfam-automation\LFAM_Automacao.project
~~~

**Não crie novo projeto com o mesmo nome** e não mova a cópia ativa enquanto o CODESYS estiver aberto. Confira a árvore: Device > Lógica CLP > Application > PLC_PRG, MainTask. A captura do notebook mostra a CPU virtual no projeto, mas não comprova execução do Ladder.

Abra o Device e faça Escanear rede; selecione o Control Win local e confirme o caminho ativo. O Gateway verde significa conectividade do Gateway, **não** necessariamente CLP ativo nem programa executando. Inicie Control Win no ícone da bandeja caso esteja parado.

Para compilar: Compilação > Compilar. Para execução, após confirmar o alvo local e autorização: Online > Login, transferir programa se solicitado, e iniciar aplicação. Capture o estado real e mensagens sem erros. Não faça download para PLC físico.

## 4. Instalar o MCP no CODESYS

Em Ferramentas > Instalador de CODESYS, selecione sua instalação, Complementos > Navegar, procure `CODESYS Development System MCP Server` e instale o 1.1.0.0. Feche CODESYS se o instalador pedir; use o Installer com privilégios adequados.

Em Ferramentas > Gestor de licenças, confirme uma licença válida para esta máquina. **Instalação do add-on ≠ licença ativa**.

Use Ferramentas > Ativar o servidor MCP. O comando é um alternador: não clique novamente se já estiver ligado.

Use Ferramentas > Configurar o cliente MCP e copie o caminho do bridge. Na captura deste notebook, o caminho era:

~~~text
D:\ProgramFilesFolder\CODESYS\CODESYS MCP Server\1.1.0.0\CodesysMCPBridge\CodesysMCPBridge.exe
~~~

O caminho é **específico desta instalação**, não deve ser copiado cegamente para outros computadores.

## 5. Registrar no Claude Code

Abra PowerShell **na raiz** do repositório (não no WSL). Se não houver `codesys-ide` já registrado:

~~~powershell
claude mcp add --scope local --transport stdio codesys-ide -- "D:\ProgramFilesFolder\CODESYS\CODESYS MCP Server\1.1.0.0\CodesysMCPBridge\CodesysMCPBridge.exe"
claude mcp list
~~~

Se já existir, examine antes com `claude mcp get codesys-ide`. Ao mudar versão/caminho, remova a entrada local antiga com `claude mcp remove codesys-ide -s local` e registre novamente.

Dentro de `claude`, digite `/mcp`. O esperado é `codesys-ide` conectado. **Configuração registrada não é evidência de conexão.**

## 6. Teste inicial não destrutivo

Peça ao agente para listar projeto, Device, Application, PLC_PRG e MainTask; identificar linguagem e listar ferramentas MCP; compilar sem alterar o projeto; registrar erros e avisos. Não pedir criação das 15 redes antes desse teste.

## 7. Preparação do SCADA

Para os componentes adicionais:

~~~powershell
python --version
node --version
npm --version
~~~

Python/FastAPI, OPC UA e React/TypeScript só entram quando houver prova real de runtime + comunicação de tags. Evitar Node-RED se não for necessário. Não instalar pacotes Python globalmente; preferir `.venv`.

## 8. Diagnóstico local

~~~powershell
.\tools\diagnose-windows.ps1
~~~

Consulte [MCP_TROUBLESHOOTING.md](MCP_TROUBLESHOOTING.md) para licença, CONNECTION_CLOSED e Smart App Control.
