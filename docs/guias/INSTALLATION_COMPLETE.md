# Guia completo de instalação — LFAM (Windows, do zero)

Objetivo: um colega com um Windows recém-preparado chega até um **programa Ladder rodando no CODESYS Control Win** e, se quiser, ao **Claude Code lendo o projeto pelo MCP**. Nada aqui depende do computador de outra pessoa.

> **Situação do material:** os links e nomes de menu abaixo foram conferidos na documentação oficial em novembro de 2026 (CODESYS Help, Store e documentação do Claude Code). Onde a instalação real pode diferir, isso está dito. **Este guia ainda não traz capturas de tela**; elas serão adicionadas só quando forem capturadas de verdade e sem dados pessoais.

## Índice

- [0. Dois modos de instalação](#0-dois-modos-de-instalação)
- [A. Preparar o computador](#a-preparar-o-computador)
- [B. Conta na CODESYS Store](#b-conta-na-codesys-store)
- [C. CODESYS Installer e Development System](#c-codesys-installer-e-development-system)
- [D. Control Win](#d-control-win)
- [E. Administrador do controlador virtual](#e-administrador-do-controlador-virtual)
- [F. Clonar e abrir o projeto LFAM](#f-clonar-e-abrir-o-projeto-lfam)
- [G. Licença gratuita para o MCP (Professional Developer Edition Demo)](#g-licença-gratuita-para-o-mcp)
- [H. Instalar o MCP do CODESYS](#h-instalar-o-mcp-do-codesys)
- [I. Claude Code e conexão com o MCP](#i-claude-code-e-conexão-com-o-mcp)
- [J. Problemas do MCP](#j-problemas-do-mcp)
- [Modo desenvolvedor: Python, Node e automação](#modo-desenvolvedor-python-node-e-automação)
- [Lista final de verificação](#lista-final-de-verificação)
- [O que depende de ação manual](#o-que-depende-de-ação-manual)
- [Glossário](#glossário)

---

## 0. Dois modos de instalação

| | **Modo integrante** | **Modo desenvolvedor** |
|---|---|---|
| Para quem | Quem vai abrir o projeto, entender o Ladder e demonstrar | Quem vai gerar redes, backend e SCADA |
| Etapas | A, B, C, D, E, F | Tudo do integrante + G, H, I e a seção de desenvolvedor |
| Claude Code / MCP | **Não precisa** | Sim |
| Licença extra | Não | Professional Developer Edition (demo gratuita de 30 dias, ver G) |
| Python / Node | Não | Python 3.12 (simulador, backend, testes) e Node LTS (SCADA web) |

Por que cada item do modo desenvolvedor existe:

- **Claude Code + MCP:** o agente lê e compila o projeto CODESYS pelo IDE. O MCP oficial só **edita Structured Text**; objetos gráficos (Ladder) são **somente leitura** para ele (documentação oficial do MCP 1.1.0.0).
- **Scripting API do CODESYS + PLCopen XML:** é o caminho que o projeto usa para **criar redes Ladder** (o MCP não cria). Já vem com o Development System.
- **Python:** simulador físico, backend FastAPI e testes automatizados.
- **Node.js:** build do SCADA web em React/TypeScript.

---

## A. Preparar o computador

### A.1 Requisitos

| Item | Mínimo | Recomendado |
|---|---|---|
| Sistema | Windows 10 ou 11, **64 bits** | Windows 11 atualizado |
| RAM | 8 GB | 16 GB |
| Disco livre | ~10 GB (CODESYS + Control Win + ferramentas) | 20 GB |
| Internet | Obrigatória para instalar, ativar licença e usar o Claude Code | — |
| Permissões | Conta com direito de **administrador** (Installer e serviço do Control Win) | — |

Valores de RAM/disco são uma estimativa prática do grupo; confirme os requisitos da sua versão na página do produto na [CODESYS Store](https://store.codesys.com/en/). O CODESYS Installer informa Windows 10/11 como sistemas suportados.

### A.2 Verificar 64 bits

```powershell
[Environment]::Is64BitOperatingSystem     # esperado: True
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, BuildNumber
```

### A.3 Obrigatório e opcional

| Obrigatório (modo integrante) | Opcional (modo desenvolvedor) |
|---|---|
| Git, VS Code, CODESYS Development System, Control Win | Claude Code, MCP, licença PDE, Python, Node.js |

### A.4 Instalar Git e VS Code

1. Baixe o Git em <https://git-scm.com/downloads> e instale aceitando as opções padrão.
2. Baixe o VS Code em <https://code.visualstudio.com/download> e instale.
3. Abra o **PowerShell**: tecla Windows → digite `PowerShell` → Enter (não precisa ser administrador para estes comandos).
4. Verifique:

```powershell
git --version
code --version
```

Esperado: um número de versão em cada comando. Se `code` não for reconhecido, feche e abra o PowerShell de novo (o PATH só atualiza em terminais novos).

Identidade Git (use **seu** nome e e-mail, apenas neste repositório, depois de clonar na etapa F):

```powershell
git config --local user.name  "SEU NOME"
git config --local user.email "SEU_EMAIL_DO_GITHUB"
```

---

## B. Conta na CODESYS Store

A conta serve para **baixar** instaladores, **fazer pedidos** (inclusive gratuitos) e **receber tickets de licença**. Ela **não** é o login do controlador virtual (ver [E](#e-administrador-do-controlador-virtual)).

1. Abra <https://store.codesys.com/en/>.
2. Clique em **Login / Create an Account** ou vá direto a <https://store.codesys.com/en/customer/account/create/>.
3. Preencha os dados pedidos (nome, e-mail e demais campos obrigatórios do formulário).
4. Escolha uma **senha forte** e guarde-a em um gerenciador de senhas. Não use a mesma de outros serviços.
5. Aceite os termos exigidos.
6. Se a Store pedir **confirmação por e-mail**, abra a mensagem e clique no link.
7. Faça login.
8. Onde achar as coisas: na área **My Account** ficam **My Orders** (pedidos), **My Downloads** (downloads) e **My Licenses/Tickets** (licenças e tickets). Os rótulos podem variar; use o FAQ oficial se não os encontrar: <https://store.codesys.com/en/frequently-asked-questions-faq>.

Cada integrante cria a **própria** conta. Nunca compartilhe senha ou ticket em chat, e-mail ou Git.

---

## C. CODESYS Installer e Development System

### C.1 O que é cada coisa

| Termo | O que é |
|---|---|
| **CODESYS Installer** | Programa gratuito que baixa, instala, atualiza e remove versões do CODESYS e de complementos. Pode também criar um "sandbox". |
| **CODESYS Development System** | O IDE onde se escreve o Ladder (este projeto usa **V3.5 SP22 Patch 4 = 3.5.22.40**). |
| **CODESYS Control Win** | Controlador virtual (CLP simulado) que roda como serviço do Windows. |
| **Add-ons** | Complementos opcionais (ex.: MCP Server). Não instale todos. |
| **License Manager (Gestor de licenças)** | Ferramenta do IDE (menu Ferramentas) para ativar licenças. |

### C.2 Instalar o CODESYS Installer

1. Abra <https://store.codesys.com/en/codesys-installer.html> (também em <https://www.codesys.com/ecosystem/services/download/>).
2. Faça login e use **Download** (produto gratuito, sem licença). Execute o instalador.
3. Abra o **CODESYS Installer** pelo menu Iniciar. Se algo falhar por permissão, clique com o botão direito → **Executar como administrador**.

### C.3 Criar a instalação do Development System

1. No Installer, procure **CODESYS Development System V3** e selecione a versão **3.5.22.40 (V3.5 SP22 Patch 4)**.
2. Escolha **64 bits** quando houver a opção.
3. Instale. O Installer baixa as dependências necessárias.
4. Feche o Installer e abra o **CODESYS** pelo menu Iniciar.
5. Confirme a versão: **Ajuda → Sobre** (Help → About). Esperado: `3.5.22.40`.

Para verificar de fora do IDE:

```powershell
.\tools\diagnose-windows.ps1 -Redact
```

(requer o repositório clonado, etapa F). O script descobre sozinho onde o CODESYS está instalado.

### C.4 Problemas conhecidos do Installer

Nenhuma das causas abaixo deve ser **assumida**: confirme com o sintoma e com o log.

| Sintoma | Possível causa | O que verificar / fazer |
|---|---|---|
| Installer abre em **modo somente leitura** | Executado sem permissão para alterar a instalação | Feche e reabra como **administrador** |
| Instalação/atualização **bloqueada** | `CODESYS.exe` está aberto | Feche o IDE (`Get-Process CODESYS`) e tente de novo |
| Falha com **código de saída `-1`** | Genérico; várias causas possíveis | **Leia o log do Installer** antes de agir. Procure no próprio Installer a opção de log/detalhes; reexecute como administrador; feche IDE e antivírus em varredura; tente de novo. Se persistir, registre a mensagem exata do log |
| **Várias versões** instaladas | Instalações paralelas | Normal. O projeto exige 3.5.22.40; confirme qual abre o `.project`. O `diagnose-windows.ps1` lista todas |

Não force: **não** é preciso instalar todos os complementos disponíveis.

---

## D. Control Win

O **Control Win V3 x64** é instalado junto com o Development System neste ambiente (o diagnóstico encontra os serviços `CODESYS Control Win V3 - x64` e `CODESYS Gateway V3`). Se na sua instalação ele não aparecer, adicione-o pelo Installer (Add-ons) ou veja a página do produto na Store.

### D.1 Cinco coisas diferentes (não confundir)

| # | Situação | Como confirmar |
|---|---|---|
| 1 | Development System instalado | `Ajuda → Sobre` mostra 3.5.22.40 |
| 2 | **Gateway** funcionando | Em *Device → Seleção de controladores* o ícone do Gateway fica verde |
| 3 | **Control Win iniciado** | Serviço em execução; ícone na bandeja ativo |
| 4 | **Comunicação** estabelecida com o dispositivo | Dispositivo aparece e fica verde; login funciona |
| 5 | Aplicação **compilada**, **transferida** e **em execução** | Compila sem erro; Online → Login; estado **RUN** na barra |

**Gateway verde ≠ CLP executando.** Só o item 5 prova que o Ladder roda.

### D.2 Iniciar e verificar o Control Win

1. O Control Win roda como **serviço**. Veja:

```powershell
Get-Service | Where-Object { $_.DisplayName -like 'CODESYS*' } | Select-Object DisplayName, Status
```

2. Procure o ícone do **CODESYS Control** na **bandeja do sistema** (perto do relógio; pode estar em "mostrar ícones ocultos"). Clique com o botão direito:
   - **Start PLC** liga o runtime (o ciclo de varredura passa a existir).
   - **Stop PLC** para o runtime. Aplicação carregada fica, mas não executa.
3. No IDE, dê duplo clique em **Device** → aba **Seleção de controladores** (Communication Settings).
4. Clique **Escanear rede** (Scan Network). O CLP local aparece com o nome do seu computador; selecione e confirme (**OK**). Isso define o **caminho de comunicação**. A ajuda oficial descreve isso como o *connection path* e não usa a expressão "caminho ativo".
5. Interprete: Gateway verde (conexão com o gateway), dispositivo verde (alcançável). Confirmação final de execução: **Online → Login** e estado RUN.

### D.3 Limite do modo demonstrativo

O Control Win sem licença funciona em **modo demonstrativo com limite de tempo de execução**; para uso contínuo é preciso licença. **Confirme o valor atual na documentação/Store do produto** — este guia não afirma um número porque não o validamos. Para demonstração acadêmica curta isso costuma bastar; planeje reiniciar o runtime quando o limite acabar.

---

## E. Administrador do controlador virtual

**Etapa obrigatória** — foi o bloqueio real do nosso CP2: o `login()` travava (em modo sem janela) porque aparecia o prompt `Prompt_ActivateUserManagement_New`: o dispositivo **exige gerenciamento de usuários** e o Control Win ainda não tinha administrador.

### E.1 Três conceitos diferentes

| Conceito | Para quê | Onde vive |
|---|---|---|
| **Conta da CODESYS Store** | Downloads, pedidos, licenças | Site da Store |
| **Licença CODESYS** | Autoriza usar produtos (ex.: MCP) | License Manager / soft container |
| **Administrador do Control Win** | Autenticar no **CLP virtual** | **Dentro do dispositivo** |

Também não confunda **gerenciamento de usuários do dispositivo** (esta etapa) com o gerenciamento de usuários **do projeto**.

### E.2 Passo a passo (conforme a ajuda oficial do CODESYS)

Fonte: <https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_configuring_connection_to_plc.html>

1. Abra `LFAM_Automacao.project` no CODESYS (etapa F).
2. Na árvore, selecione o dispositivo **Device (CODESYS Control Win V3 x64)** → menu **Projeto → Editar objeto** (ou duplo clique).
3. Aba **Communication Settings / Seleção de controladores**.
4. Clique em **Scan Network / Escanear rede**.
5. Selecione o controlador **local** na lista e **OK**.
6. Aparece a pergunta de que o dispositivo exige gerenciamento de usuários, ainda desativado. Clique **Sim / Yes**.
7. Em **Add Device User** informe **nome** e **senha** do administrador e marque *Password can be changed by the user*; **OK**.
8. Em **Device User Logon** entre com o administrador que acabou de criar.
9. Conexão estabelecida.

### E.3 Cuidados

- Use **senha forte**. **Guarde-a em gerenciador de senhas.** A ajuda oficial avisa que **não existe recuperação** da senha de um dispositivo pelo IDE.
- **Nunca** envie a senha para o Claude/IA, Git, chat ou captura de tela.
- **Não desative** a exigência de autenticação para "contornar"; crie o administrador.
- Os scripts do repositório que fazem login online aceitam as credenciais pelo diálogo do IDE; não grave senha em arquivo.

---

## F. Clonar e abrir o projeto LFAM

1. **Acesso:** o repositório é **privado**. Peça ao dono para te adicionar como colaborador no GitHub e aceite o convite. Faça login no Git (o Git Credential Manager abre o navegador na primeira vez).
2. **Clone** onde quiser (a pasta é livre):

```powershell
cd $HOME\Documents          # ou qualquer pasta
git clone https://github.com/Soturine/lfam-automation.git
cd lfam-automation
```

3. **VS Code:** `code .`
4. **CODESYS:** abra `LFAM_Automacao.project` (Arquivo → Abrir projeto). **Não crie outro projeto com este nome.**
5. **Confira a árvore:** `Device (CODESYS Control Win V3 x64)` → `Lógica CLP` → `Application` → `PLC_PRG` e `Configuração de tarefas → MainTask → PLC_PRG`.
6. **Compilar:** Compilação → Compilar. Esperado: **0 erros**.
7. **Login:** Online → Login (se for a primeira vez, siga a etapa E). Responda **Não** se o CODESYS perguntar se deseja **apagar aplicações de terceiros**.
8. **Transferir** a aplicação quando perguntado e **somente** para o Control Win local.
9. **Iniciar:** Depuração → Iniciar (ou o botão ▶). A barra deve mostrar **RUN**.
10. **Observar:** abra `PLC_PRG` e veja valores ao vivo (Online). Force `TRUE` em uma entrada e veja a bobina mudar.

**Projeto original × POCs:** `LFAM_Automacao.project` (raiz) é o projeto do grupo e **não deve ser sobrescrito por scripts**. Os scripts em `tools/codesys_scripts/` trabalham em **cópias** dentro de `work/` (ignorada pelo Git).

Arquivos `.opt`, `.~u` e caches são locais e ignorados pelo Git.

---

## G. Licença gratuita para o MCP

### G.1 O que é e por quê

A **CODESYS Professional Developer Edition (PDE)** é um pacote de complementos (SVN, Static Analysis, Test Manager, UML, Profiler, Git, File-Based Storage e **Development System MCP Server**). **O MCP Server precisa de licença**; a PDE Demo é gratuita e dura **30 dias**, anunciados na página do produto. Não presuma que ela esteja disponível ou seja renovável: confira antes.

- Produto: <https://store.codesys.com/en/codesys-professional-developer-edition-demo.html>
- Requisito informado na página: Development System **3.5 SP19 Patch 3 ou superior**. Cada pacote é instalado individualmente.
- Licenciamento por **soft container** (ou dongle opcional).
- Suporte técnico **não** está incluso.

### G.2 Obter o Ticket ID

1. Faça login na Store ([etapa B](#b-conta-na-codesys-store)).
2. Abra a página do produto acima, adicione ao carrinho (**€ 0,00**) e finalize o pedido gratuito.
3. O **ticket** chega no e-mail de confirmação e aparece na sua conta. (A página do produto não detalha como o ticket é entregue; é o que a documentação de ativação descreve: "a confirmação por e-mail contém o número do ticket").

### G.3 Ativar (Workstation, sem servidor de licenças)

Fonte: <https://content.helpme-codesys.com/en/Lizenzierung/_license_howto_without_license_server_workstation.html>

1. Abra o CODESYS.
2. **Ferramentas → Gestor de licenças** (Tools → License Manager).
3. Selecione **Workstation** → **Avançar**.
4. Na visão geral, **Install Licenses** (Instalar licenças).
5. Escolha **Activate license** → **Avançar**.
6. Em **Ticket ID** informe o ticket. O servidor vem preenchido como `license.codesys.com`; o **contêiner** (soft container) aparece sozinho após digitar o ticket.
7. **Avançar**: a ferramenta contata o servidor e ativa.
8. **Concluir**. O Gestor de licenças passa a listar as licenças no contêiner.

A ativação descrita é **online** (a página não descreve método offline).

### G.4 Verificar

- No **Gestor de licenças**, a licença do MCP Server aparece no contêiner.
- Após [H](#h-instalar-o-mcp-do-codesys), `Ferramentas → Ativar servidor MCP` deve iniciar sem erro de licença.

### G.5 Diagnóstico de licença

| Sintoma | Verificar |
|---|---|
| Ticket inválido | Copie o ticket exatamente do e-mail, sem espaços; confirme que é de PDE/MCP |
| Ticket já ativado | Já foi usado (nesta ou em outra máquina); veja a conta na Store |
| Licença ausente | O pedido foi concluído? O ticket chegou? O container aparece no Gestor? |
| Licença incompatível | Produto ou versão do IDE diferente do que a licença cobre (PDE exige 3.5 SP19 P3+) |
| Dependências ausentes | O add-on do MCP foi instalado? Reinstale pelo Installer |
| Contêiner inadequado | Selecione o soft container correto na ativação |
| Erro de servidor de licenças | Sem internet/proxy/firewall; tente outra rede e reabra o assistente |
| Avaliação expirada | Passaram 30 dias; um novo pedido pode não ser possível. **Não compre licença paga sem avaliar alternativas**: o modo integrante nem precisa de MCP |

**Nunca** grave ticket, chave ou arquivo de licença no repositório.

---

## H. Instalar o MCP do CODESYS

Docs: <https://content.helpme-codesys.com/en/CODESYS%20Development%20System%20MCP%20Server/index.html> · Habilitar: <https://content.helpme-codesys.com/en/CODESYS%20Development%20System%20MCP%20Server/_idemcp_cmd_enable_mcp_server.html>

1. Feche o CODESYS (o Installer não altera uma instalação aberta).
2. Abra o **CODESYS Installer** (como administrador, se necessário) e selecione sua instalação 3.5.22.40.
3. Abra **Add-ons** (Complementos) e pesquise `CODESYS Development System MCP Server`.
4. Selecione a versão compatível (**1.1.0.0**, documentação de julho de 2026) e instale com as dependências.
5. Reinicie o ambiente se solicitado, abra o CODESYS e confirme que o complemento aparece instalado.
6. **Ferramentas → Ativar servidor MCP** (Tools → Enable MCP Server). É um **alternador**: ícone indica ligado/desligado; clicar de novo desliga.

Três coisas diferentes:

| | Significa | Como saber |
|---|---|---|
| **Complemento instalado** | Arquivos presentes | Installer; menu Ferramentas tem os comandos MCP |
| **Servidor habilitado** | Backend ouvindo | Ícone da barra de ferramentas ligado |
| **Licença válida** | Autorizado a rodar | Gestor de licenças ([G](#g-licença-gratuita-para-o-mcp)) |

Só **uma instância** do servidor MCP pode estar habilitada por vez; várias instâncias do CODESYS com o servidor ligado não são suportadas.

**Privacidade (da documentação oficial):** com modelos em nuvem, **tudo o que o MCP puder ler do projeto é enviado ao provedor**. O projeto LFAM é acadêmico; antes de usá-lo, confirme que o grupo concorda.

---

## I. Claude Code e conexão com o MCP

Docs: <https://code.claude.com/docs/en/setup> · MCP: <https://code.claude.com/docs/en/mcp>

Requer conta Claude Pro/Max/Team/Enterprise ou Console (o plano gratuito não inclui Claude Code).

### I.1 Instalar

Instalação nativa (recomendada pela documentação), no **PowerShell**:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Alternativa WinGet (não atualiza sozinho; use `winget upgrade Anthropic.ClaudeCode`):

```powershell
winget install --id Anthropic.ClaudeCode -e
```

Abra um **novo** PowerShell e confira:

```powershell
claude --version
claude doctor
```

Autentique: rode `claude` e siga o navegador.

### I.2 Obter o caminho do bridge

No CODESYS: **Ferramentas → Configurar o cliente MCP** (Tools → Configure MCP Client). A janela mostra o **caminho atual do `CodesysMCPBridge.exe`** (inclui a pasta da versão; muda a cada atualização). O comando **não** configura o cliente: você copia o caminho.

Atalho: `.\tools\diagnose-windows.ps1` lista os bridges encontrados.

### I.3 Registrar no Claude Code

No PowerShell, **na pasta do repositório** (escopo `local` guarda por projeto, só para você, sem ir para o Git):

```powershell
claude mcp add --scope local --transport stdio codesys-ide -- "CAMINHO_REAL_DO_BRIDGE"
claude mcp list
```

`list` deve mostrar `codesys-ide ... Connected`. Isso prova só a **conexão de transporte**.

### I.4 Teste real

```powershell
claude
```

Dentro da sessão, digite `/mcp` (**não é comando do PowerShell**; é comando dentro do Claude Code). Deve listar `codesys-ide` com a contagem de ferramentas. Então peça: *"Use o codesys-ide para listar a árvore do projeto."* Esperado: `Device → Plc Logic → Application → PLC_PRG, Task Configuration → MainTask`. **Só isso comprova uma leitura real**.

Se você registrou o MCP com a sessão do Claude aberta, **reinicie a sessão**: as ferramentas só carregam na abertura.

### I.5 Limites do MCP e como o projeto os contorna

O MCP oficial lê árvore, edita **Structured Text**, gerencia bibliotecas e dá diagnóstico de compilação. **Não cria nem edita Ladder gráfico.** O projeto usa **importação PLCopen XML** via **Scripting API oficial** do CODESYS (`tools/codesys_scripts/`, `codesys/exports/`) e usa o MCP para **inspeção e compilação**. Veja `docs/evidence/CP2_LD_POC.md`.

---

## J. Problemas do MCP

Legenda: ✅ observado neste projeto · ❓ hipótese não comprovada.

| Sintoma | Causas possíveis | Diagnóstico | Solução |
|---|---|---|---|
| `claude` não reconhecido | Não instalado; terminal antigo | `Get-Command claude` | Instale (I.1); abra novo terminal |
| PATH não atualizado | Terminal aberto antes da instalação | Reabra | Feche e abra o PowerShell/VS Code |
| `É impossível iniciar o servidor MCP. Ative sua licença` | Sem licença MCP | Gestor de licenças | [Etapa G](#g-licença-gratuita-para-o-mcp) |
| Servidor MCP desabilitado ✅ | Não ligado no IDE | Ícone/menu | **Ferramentas → Ativar servidor MCP** |
| `CONNECTION_CLOSED` ✅ | Genérico: licença, servidor desligado, bridge errado, DLL bloqueada | `claude --debug-file "$env:TEMP\claude-mcp.log"` e leia o log | Corrija a causa **encontrada no log** |
| Bridge incorreto/desatualizado | Atualizou o add-on; caminho mudou | Reabra *Configurar o cliente MCP* | `claude mcp remove codesys-ide -s local` e registre de novo |
| Conectado, mas sem ferramentas ✅ | Sessão do Claude aberta antes do registro | `/mcp` | **Reinicie a sessão** |
| Ferramentas negadas | Permissões do Claude Code | Pedido de permissão na sessão | Aprove a ferramenta (leitura) |
| DLL bloqueada ✅ (em outro PC) | Política de aplicativos; evento CodeIntegrity 3077; erro `0x800711C7` | Visualizador de Eventos → CodeIntegrity; `Get-AuthenticodeSignature` | **Smart App Control não aceita exceção por DLL.** Use outro PC ou fale com o suporte CODESYS. **Não desligue o antivírus inteiro** |
| MCP em outra instância | Dois IDEs com servidor ligado | Feche um | Mantenha **uma** instância |
| `NotSigned` na DLL | Informação, não prova de bloqueio | `diagnose-windows.ps1` | Na máquina do autor a conexão **funcionou** apesar disso; não desative proteção preventivamente |

Histórico (comprovado em **outro** computador, não neste): `CONNECTION_CLOSED` com `Could not load file or assembly 'ModelContextProtocol.Core.dll'` e `0x800711C7`, Smart App Control ativo. Isso **não** implica o mesmo problema em outra máquina.

---

## Modo desenvolvedor: Python, Node e automação

```powershell
winget install --id Python.Python.3.12 -e    # ou instalador de https://www.python.org/downloads/windows/
winget install --id OpenJS.NodeJS.LTS -e     # ou https://nodejs.org/en/download
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest tests -q                    # esperado: todos passam
```

Scripts do CODESYS (trabalham em cópias do projeto, nunca no original):

```powershell
$env:LFAM_WORK = (Resolve-Path .\work)       # pasta de trabalho local
.\tools\run-codesys-script.ps1 -Script .\tools\codesys_scripts\probe_export.py
```

O script descobre sozinho o `CODESYS.exe`; use `-Exe` se houver várias instalações.

---

## Lista final de verificação

- [ ] `git --version` e `code --version` funcionam
- [ ] Conta da CODESYS Store criada e login feito
- [ ] CODESYS **3.5.22.40** abre (Ajuda → Sobre)
- [ ] Serviço do Control Win em execução; ícone na bandeja
- [ ] Administrador do dispositivo criado e login feito (etapa E)
- [ ] Repositório clonado; `LFAM_Automacao.project` abre; árvore confere
- [ ] **Compila com 0 erros**
- [ ] Aplicação **transferida e em RUN** no Control Win local
- [ ] Valor de uma variável observado mudando online
- [ ] *(dev)* Licença PDE ativa no Gestor de licenças
- [ ] *(dev)* Servidor MCP ativado; `claude mcp list` mostra `codesys-ide` conectado
- [ ] *(dev)* `/mcp` lista ferramentas e a árvore do projeto foi lida

## O que depende de ação manual

Criar conta e confirmar e-mail · pedido gratuito e ticket · ativar licença · criar a senha do administrador do dispositivo · aceitar convite do GitHub · autenticar o Claude Code · ligar o servidor MCP no IDE.

## Glossário

**CLP/PLC** controlador lógico programável · **Ladder (LD)** linguagem gráfica de contatos e bobinas · **ST** Structured Text · **IEC 61131-3** padrão das linguagens · **Control Win** CLP virtual · **Gateway** serviço que conecta o IDE aos controladores · **Runtime** programa que executa a aplicação no controlador · **MCP** protocolo que deixa um agente de IA usar ferramentas · **Bridge** executável que liga o Claude ao servidor MCP do CODESYS · **PLCopen XML** formato de intercâmbio de projetos IEC · **Soft container** arquivo de licença no PC · **Ticket ID** código de ativação de licença.
