# CP3 - transporte HMI <-> Control Win: analise (2026-11-11)

**Status: BLOQUEADO para OPC UA nesta instalacao. Nenhuma integracao real HMI->CLP foi feita. O SCADA esta em modo DEMO.**

## Observado (executado)
- Pasta do runtime (`GatewayPLC`, servico "CODESYS Control Win V3 - x64"): sem DLL/componente de servidor OPC UA (`CmpOPCUA*` ausente);
  `CODESYSControl.cfg` sem referencia a OPC UA. O IDE tem so a infraestrutura de *Symbol Configuration* / publicacao de simbolos
  (DLLs `OpcUaSymbolPublishing`, `OpcUaDataModel`), que depende de um servidor no runtime.
- O que FUNCIONA e ja foi comprovado: acesso programatico a variaveis pelo **CODESYS Scripting API** (`online.create_online_application`,
  `set_prepared_value`, `write_prepared_values`, `read_value`) com login do administrador do dispositivo - ver `CP2_LD_POC.md`.
  Roda dentro do IDE logado (a senha nao pode ficar em script versionado).

## Alternativas (nao testadas, com riscos)
| Opcao | Como | Pro | Contra / pendencia |
|---|---|---|---|
| A. Servidor OPC UA do runtime | Produto/licenca adicional para Control Win; Symbol Configuration no projeto | Padrao, o que a arquitetura previa | Nao instalado; custo/licenca; decisao do dono |
| B. Ponte via Scripting API | Processo do IDE executando script que le/escreve tags e conversa com o backend (ex.: HTTP local) | Usa so o que ja funciona | Exige IDE aberto e logado; senao precisa de credenciais fora do Git; nao e um protocolo industrial |
| C. Modbus TCP slave no projeto | Adicionar dispositivo Modbus ao projeto e cliente pymodbus no backend | Protocolo industrial, sem IDE | Altera a arvore do projeto; licenciamento do componente nao verificado; mapa de registradores a definir |

## Recomendacao
Para a demonstracao academica: manter DEMO como padrao, e oferecer o modo CLP via **B** com o IDE logado (honesto, rotulado "ponte via IDE").
A decisao entre A/B/C e do grupo (custo, licenca, alteracao do projeto). Ate la, a API retorna `mode: "DEMO"`, `plc_connected: false`.
