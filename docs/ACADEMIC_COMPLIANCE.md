# Conformidade com o enunciado da professora

Fonte: `references/ENUNCIADO_PROFESSORA.md` (transcrição; **confira mudanças no AVEA**). Entrega indicada: **27/11/2026, 00:00**.
Esta lista mostra **o que existe no repositório**; a **monografia manuscrita** e a apresentação oral são trabalho do grupo.

| Exigência | Onde está | Estado |
|---|---|---|
| Descrição do processo, objetivos, arquitetura | `references/documents/Arquitetura_Lista_ES_v2.docx`, `docs/ARCHITECTURE.md` | Existe (grupo); arquitetura integrada em `ARCHITECTURE.md` |
| Escolha e justificativa do CLP; módulos e reserva | Arquitetura v2 (S7-1200 1214C + SM 1231 TC + SM 1223) | Existe. **Diferença a declarar:** demonstração roda em **CODESYS Control Win** (simulação virtual) |
| E/S digitais, analógicas e termopares | Arquitetura v2; `docs/tags.csv` (97 tags) | Existe; `tags.csv` precisa receber as variáveis novas |
| Sensores, atuadores, motor, inversor, SSR, relés, contatores | Arquitetura v2 (tabela de dispositivos) | Existe (grupo) |
| Estratégia: PID por zona, IR, histerese, sequenciamento, TON, velocidade e pressão | Monografia; programa em `codesys/generator`; `evidence/CP4_NETWORKS_STATUS.md` | Programa implementado e **compilado**; PID com ganhos hipotéticos |
| Redes e protocolos (efetivos × propostos) | Arquitetura v2 (PROFINET proposto); `CP3_PLC_MODE.md` | **Efetivo:** OPC UA cliente, **testado contra o Control Win** (Basic256Sha256 SignAndEncrypt); **proposto:** PROFINET (não testado, não simulado) |
| SCADA/HMI com seis telas, interação, histórico e alarmes | `scada/web`, `evidence/scada/*.png` | **Funciona em DEMO**; modo CLP pendente |
| Segurança, intertravamentos, análise de falhas | Arquitetura v2 (15 intertravamentos), redes 02/03/04 | Existe; tabela de falhas (efeito/detecção/resposta) é tarefa 12 do grupo |
| Fluxograma, esquema elétrico | `references/visual/fluxograma_funcional.png`, `Esquema_Eletrico.docx` | Existem (grupo, preliminares). **Pendência:** tensão 220 V mono × trifásico |
| **Ladder real diretamente ligado ao processo** | `codesys/exports/LFAM_PROGRAM.xml` importado em `LFAM_Automacao.project`-cópia; POC executada | **Atendido pela POC executada no Control Win** (`CP2`). Programa completo compilado **e executado** no Control Win (CP3, `evidence/CP3_ROUNDTRIP_OK.txt`) |
| Monografia manuscrita; apresentação de 20 min; arguição | `docs/ROTEIRO_APRESENTACAO.md` | **Só o roteiro e as perguntas** estão prontos; o texto manuscrito é do grupo |
| Interação hardware × software × processo | `docs/ARCHITECTURE.md`, `ROTEIRO_APRESENTACAO.md` | Explicado (sensor → CLP → Ladder → atuador → HMI) |
| Grupo multidisciplinar, participação de todos | Arquitetura v2 (divisão) | Todos devem dominar o projeto inteiro |

## O que dizer (e o que NÃO dizer) na apresentação
- Dizer: "Ladder **gráfico** gerado e **executado** no CODESYS Control Win (POC); programa completo **compilado**; SCADA em **modo demonstração** com planta simulada."
- Dizer também: "o SCADA em modo PLC lê e comanda o Ladder rodando no Control Win via OPC UA; as entradas ainda vêm da planta simulada".
- Não dizer: "PID sintonizado" (ganhos hipotéticos), "validado no S7-1200".
- A emergência é **hardware independente**; a interface web não é parada de emergência.
