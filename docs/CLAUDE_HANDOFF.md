# Handoff para Claude Code

## Contexto

Repositório privado `Soturine/lfam-automation`. **Não** recriar o projeto CODESYS: abrir `LFAM_Automacao.project` na raiz, analisar antes de alterar. Windows nativo, CODESYS V3.5 SP22 Patch 4, Control Win V3 x64, MCP Server 1.1.0.0.

A tela de configuração MCP no notebook mostra o bridge em:

~~~text
D:\ProgramFilesFolder\CODESYS\CODESYS MCP Server\1.1.0.0\CodesysMCPBridge\CodesysMCPBridge.exe
~~~

Esse caminho não deve ser commitado em configuração MCP compartilhada. Verificar o estado de licença e servidor **nesta máquina**. A conexão MCP só está comprovada quando `claude mcp list` e leitura efetiva do projeto funcionarem.

## Instrução inicial ao agente

Inspecione `README.md`, `docs/`, `LFAM_Automacao.project`, `git status` e o ambiente local. Preserve trabalho existente. Primeiro faça diagnóstico não destrutivo do MCP: confirmar licença/servidor, ler árvore do projeto, identificar linguagem real do `PLC_PRG`, verificar compilação e disponibilidades da API. Registre o que foi observado, sem inventar acesso ou sucesso.

Depois realize uma POC: gerar/importar UMA rede Ladder real, compilar, executar no Control Win e observar a variável. Se o MCP oficial não oferecer escrita de Ladder gráfico, avalie importação CODESYS XML/PLCopen XML ou automação da IDE. **Não substitua a exigência Ladder por Structured Text sem registrar a diferença e obter decisão.**

Somente após POC válida, avance para 15 redes, gateway OPC UA condicionado a runtime compatível, FastAPI/WebSocket e SCADA React. Modos Demo e PLC separados. O runtime controla estados e permissivos, HMI apenas solicita comandos.

Trabalhe com checkpoints e testes executados, documentação de bloqueios, correções e evidências. Não faça mudanças em máquinas físicas. Não instale dependências globalmente sem justificativa. Preserve privacidade, segredos, licenças e materiais do grupo.

No Git, use apenas identidade local do dono do repositório, nenhum Co-Authored-By de IA, não crie PR sem pedido, evite workflows CI desnecessários e só envie à `main` após validação.

## Acesso e limitações

- MCP do CODESYS: leitura/navegação, ST, compilador e documentação; não assumir criação gráfica de Ladder/HMI.
- CODESYS Control Win virtual: não é Siemens S7-1200; validar mapeamento E/S e blocos.
- GitHub atual: arquivo `.project` real está na raiz. Os temporários devem permanecer ignorados.
- Sem conexão comprovada, nenhuma alegação de SCADA online, PIDs validados ou runtime rodando.
