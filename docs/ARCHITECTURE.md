# Arquitetura proposta — extrusora LFAM

## Premissas verificadas

- Projeto CODESYS em `LFAM_Automacao.project` (raiz); configuração do dispositivo mostra `CODESYS Control Win V3 x64`.
- Arquitetura acadêmica de referência: Siemens S7-1200 CPU 1214C DC/DC/DC, termopares, entradas analógicas, motor/inversor, robô e SCADA.
- **Não tratar endereços Siemens I/Q/M como mapeamento automaticamente válido no Control Win.** Criar GVL e contratos tipados com mapemento explícito para simulação, em vez de reutilizar endereços sem validação.
- Nenhuma medição física, comunicação OPC UA ou malha PID foi ainda verificada nesta versão do projeto.

## Fluxo pretendido

~~~text
Claude Code (Windows, desenvolvimento)
     |
     | MCP local -> CODESYS IDE (projeto, diagnósticos, ferramentas)
     v
CODESYS IDE -> Control Win (Ladder / runtime virtual)
                      |                 ^
           estados e comandos           | sinais de processo virtuais
                      v                 |
        Gateway de comunicação     Modelo didático LFAM
           OPC UA (a validar)      temperaturas, rosca, pressão
                      |
                 FastAPI
           (contrato de tags,
        validação, logs, WebSocket)
                      |
              React / TypeScript
        HMI/SCADA web com 6 telas
~~~

O navegador não deve escrever diretamente em variáveis perigosas do CLP. O backend envia solicitações validadas e confirma o estado real após leitura do controlador. Proteções críticas permanecem independentes da camada web.

## Separação de responsabilidades

- **CODESYS / Ladder:** estados, permissivos, sequências, temporizadores, selos, alarmes e comandos permitidos.
- **Simulador de planta:** evolução de temperatura, pressão, rotação, inércia, ruído e falhas; NÃO decide permissivos.
- **Gateway:** transporte seguro das tags, reconexão, timeout, heartbeat, identificação de origem e auditoria de comandos.
- **HMI:** sinótico, operadores, setpoints permitidos, alarmes, gráficos e receitas; sem duplicar a lógica de segurança.
- **Demo offline:** simulador desacoplado claramente rotulado; jamais exibir dados demo como medições de CLP.
- **Modo PLC:** estado só fica verde/conectado com leitura válida de runtime e resposta às operações.

## Domínios do processo

1. Zonas térmicas Z1–Z5: termopares, SSR, controle PID com limites e diagnósticos.
2. Câmara de resfriamento: histerese e falha de condição térmica.
3. Encharque térmico de 15 minutos: readiness condicionada a todas as zonas.
4. Alimentação/dosador: funil, contagem de ciclos, ausência de material.
5. Rosca e inversor: partida/parada manual e automática, ventilação, faixa de velocidade.
6. Pressão: pré-alarme 16,5 MPa e intertravamento 17 MPa (revisar lógica e prioridades).
7. IR/deposição e interface com robô: sinais de prontidão e movimento.
8. Falhas: sobretemperatura, termopar, ventilação, contator colado, reset condicionado.

## Contrato de dados

Definir `docs/tags.csv` ou esquema versionado com nome lógico, tipo IEC, unidade, faixa, origem, sentido de escrita, valor inicial, qualidade e atualização. Implementar conversão para as variáveis reais apenas após inspeção do projeto.

Exemplos de tags propostas a validar: `TT_Z1..TT_Z5`, `PT_FUNDIDO_MPA`, `EST_AQUEC`, `EST_EXTRUSAO`, `FALHA_GERAL`, `INV_RUN`, `INV_REF_RPM`.

## Riscos de integração a verificar

- `SM0.0` não é bit ALWAYS_TRUE nativo do S7-1200; revisar o esquema original.
- A detecção de termopar rompido deve usar diagnóstico do módulo específico; comparação genérica com 32767 não é suficiente para todo hardware.
- Controlar uma saída com múltiplas redes (ex.: `QW70`) exige arbitragem explícita.
- Não ligar diretamente `PID_Compact` Siemens a um runtime CODESYS sem adaptação e validação de bibliotecas.
- `M2.0..M2.4` e cinco comparadores devem ser representados como cinco resultados explícitos ou redução apropriada.
- Entradas de emergência devem seguir lógica fail-safe e independência funcional; um bit de software não certifica segurança.

Tudo acima é **escopo proposto**, não prova de implementação.
