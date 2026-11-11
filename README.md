# LFAM Automation

Projeto acadêmico de automação de uma extrusora LFAM (Large Format Additive Manufacturing), com programação IEC 61131-3 em Ladder, CLP virtual CODESYS, proposta de supervisório web e modelo didático do processo.

> **Estado atual (novembro de 2026):** POC de 1 rede Ladder **executada e confirmada** no Control Win (CP2). 35 redes (70 elementos) geradas por script, **compiladas sem erro**, ainda **sem execução online** no runtime (só a POC); rede 14 (CTU) e PID real pendentes. Simulador físico, backend FastAPI e SCADA React de 6 telas funcionam em **modo DEMO** com testes (pytest + Playwright). **Modo CLP não implementado**: o runtime desta instalação não tem servidor OPC UA (ver `docs/evidence/CP3_TRANSPORT_ANALYSIS.md`).

## Projeto existente

- **Arquivo CODESYS:** [LFAM_Automacao.project](LFAM_Automacao.project), na raiz do repositório.
- **Ambiente de desenvolvimento:** CODESYS V3.5 SP22 Patch 4 (3.5.22.40).
- **Alvo de testes:** CODESYS Control Win V3 x64, quando instalado e iniciado.
- **Integração com IA:** CODESYS Development System MCP Server 1.1.0.0 + Claude Code, condicionada a licença, ativação do servidor e conexão validada.
- **Git:** branch principal main; repositório privado inicialmente.

O estudo original menciona Siemens S7-1200 CPU 1214C DC/DC/DC. **CODESYS Control Win não é um S7-1200**: o projeto virtual precisa de mapeamento próprio de E/S e validação antes de qualquer eventual migração ao TIA Portal.

## Objetivos

1. Modelar o processo: aquecimento em cinco zonas, encharque, resfriamento, rosca, dosagem, interface com robô, pressão e falhas.
2. Implementar **redes Ladder gráficas reais** (não apenas imagens ou código ST equivalente) e comprovar sua compilação/execução.
3. Criar uma HMI/SCADA web com estados confirmados pelo controlador, comandos, gráficos, alarmes, receitas e histórico.
4. Integrar por gateway seguro, preferencialmente OPC UA + FastAPI + WebSocket, **após validar suporte do runtime**.
5. Criar simulador físico didático e teste ponta a ponta sem confundir dados fictícios com sinais do CLP.

## Documentação

- **[Guia completo de instalação (comece aqui)](docs/INSTALLATION_COMPLETE.md)** — do zero até o Ladder rodando no Control Win
- [Retomada rápida no Windows](docs/SETUP_WINDOWS.md)
- [MCP do CODESYS: configuração e diagnóstico](docs/MCP_TROUBLESHOOTING.md)
- [Arquitetura e responsabilidades](docs/ARCHITECTURE.md)
- [Plano de entrega, redes e telas](docs/DELIVERY_PLAN.md)
- [Executar o SCADA (DEMO)](docs/SCADA_RUN.md) · [Inventário das redes](docs/evidence/CP4_NETWORKS_STATUS.md) · [Reconciliação das fontes](docs/SOURCE_RECONCILIATION.md)
- [Instruções para Claude Code](docs/CLAUDE_HANDOFF.md)

Diagnóstico local (descobre o ambiente sozinho), no PowerShell aberto na raiz:

~~~powershell
.\tools\diagnose-windows.ps1
~~~

## Fluxo de trabalho

1. Salvar o projeto no CODESYS e fechar o editor antes de operações Git potencialmente conflitantes.
2. Executar `git status` antes de `git pull --ff-only`.
3. Confirmar Control Win, licença MCP e estado do servidor.
4. Testar leitura não destrutiva do projeto pelo Claude.
5. Validar **uma rede Ladder + um comando/estado HMI**, depois ampliar o sistema.
6. Registrar evidências reais de compilação, testes e comunicação em docs/evidence.

Arquivos de usuário e cache do CODESYS (OPT, ~u, precompilecache) não são fonte do projeto e são ignorados.

## Segurança e escopo

Este repositório é um **projeto educacional / simulador**. HMI e software de controle comum não substituem circuito de parada de emergência, dispositivos de segurança certificados, análise de riscos ou testes da máquina real. Nunca escrever comandos de máquina física sem avaliação e autorização. Não armazenar segredos, chaves, tickets de licença ou caminhos privados de MCP em arquivos versionados.

## Contexto acadêmico

Trabalho multidisciplinar de Automação Industrial: monografia escrita à mão, apresentação oral de 20 minutos e arguição. O protótipo deve relacionar hardware, software e processo físico. A proposta visual não substitui demonstrações executáveis.

Licenciamento dos materiais de terceiros, anexos e eventual publicação pública devem ser revisados antes de alterar a visibilidade do repositório.
