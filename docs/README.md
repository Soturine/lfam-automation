# Documentação do LFAM Automation

Escolha a trilha pelo **seu objetivo**. Todos os links abaixo funcionam a partir desta pasta.

```
docs/
├── entender/    COMO o projeto funciona (comece aqui)
├── guias/       COMO instalar, abrir e rodar
├── academico/   Trabalho da disciplina: perguntas, roteiro, conformidade, fontes
├── projeto/     O que foi feito: relatório, auditoria, plano, lista de variáveis
├── evidence/    Provas (logs, capturas, resultados de ensaio)
└── media/       Imagens e GIFs usados nos documentos
```

## Trilhas de leitura

### 1. "Nunca vi este projeto" (10 min)
1. [Como o projeto funciona](entender/COMO_FUNCIONA.md) — o que é, as peças, como a tela controla o Ladder, real × simulado, glossário
2. [Galeria do SCADA](entender/GALERIA.md) — as telas e as animações
3. [Perguntas e respostas](academico/PERGUNTAS_E_RESPOSTAS.md) — as dúvidas mais comuns, com respostas diretas

### 2. "Quero rodar no meu PC"
1. [Início rápido](guias/INICIO_RAPIDO.md) — 3 níveis: ver a tela (DEMO), rodar testes, ligar ao CLP
2. [Executar o SCADA](guias/SCADA_RUN.md) — variáveis de ambiente, modo apresentação, testes
3. Se for usar o CODESYS: [Instalação completa](guias/INSTALLATION_COMPLETE.md) → [Modo PLC](guias/MODO_PLC.md)
4. Deu erro? [Como o backend se liga ao CODESYS](entender/LIGACAO_BACKEND_CODESYS.md) (tabela de erros reais) · [Solução de problemas do MCP](guias/MCP_TROUBLESHOOTING.md) · [Retomada rápida no Windows](guias/SETUP_WINDOWS.md)

### 3. "Preciso entender o Ladder"
1. [O Ladder explicado](entender/LADDER_EXPLICADO.md) — como ler, ciclo de varredura, máquina de estados, rede por rede
2. [Catálogo do Ladder](entender/LADDER.md) — imagens das 15 redes
3. [Arquitetura](entender/ARCHITECTURE.md) — camadas, decisões de projeto, o que a arquitetura não é

### 4. "Vou apresentar / ser arguido" (grupo e professora)
1. [Perguntas e respostas](academico/PERGUNTAS_E_RESPOSTAS.md) — ~60 perguntas por tema, mais as "armadilhas"
2. [Roteiro da apresentação](academico/ROTEIRO_APRESENTACAO.md) — 20 min, quem fala o quê, demonstração de 2 minutos
3. [Conformidade com o enunciado](academico/ACADEMIC_COMPLIANCE.md) — o que existe × o que é do grupo
4. [Reconciliação das fontes](academico/SOURCE_RECONCILIATION.md) — divergências entre prancha, monografia e arquitetura, e a decisão de cada uma

### 5. "Quero saber o que foi feito e provado"
1. [Relatório de implementação](projeto/IMPLEMENTATION_REPORT.md) — requisito → implementação → teste → evidência → status
2. [Evidências](evidence/) — [ida e volta tela↔CLP](evidence/CP3_ROUNDTRIP_OK.txt), [cenários no CLP](evidence/CP4_ONLINE_SCENARIOS.txt), [PID real × modelo](evidence/CP4_PID_COMPARE.txt), [capturas do SCADA](evidence/scada/)
3. [Auditoria de testes e gerador](projeto/AUDIT_TESTS_AND_GENERATOR.md)
4. [Lista de variáveis (tags.csv)](projeto/tags.csv)

## Índice completo

| Documento | Para quê | Pasta |
|---|---|---|
| [COMO_FUNCIONA](entender/COMO_FUNCIONA.md) | Visão geral em linguagem simples, fluxo tela → Ladder, glossário | entender |
| [LADDER_EXPLICADO](entender/LADDER_EXPLICADO.md) | Cada etapa do Ladder e por que existe | entender |
| [LADDER](entender/LADDER.md) | Imagens das 15 redes (geradas do mesmo modelo) | entender |
| [LIGACAO_BACKEND_CODESYS](entender/LIGACAO_BACKEND_CODESYS.md) | A ponte OPC UA, segurança e erros comuns | entender |
| [ARCHITECTURE](entender/ARCHITECTURE.md) | Arquitetura técnica e decisões | entender |
| [GALERIA](entender/GALERIA.md) | Telas e animações do SCADA | entender |
| [INICIO_RAPIDO](guias/INICIO_RAPIDO.md) | Rodar em outro PC (DEMO, testes, CLP) | guias |
| [INSTALLATION_COMPLETE](guias/INSTALLATION_COMPLETE.md) | Instalar o CODESYS e o ambiente do zero | guias |
| [MODO_PLC](guias/MODO_PLC.md) | Ligar o SCADA ao Ladder no Control Win | guias |
| [SCADA_RUN](guias/SCADA_RUN.md) | Executar o SCADA, variáveis e testes | guias |
| [SETUP_WINDOWS](guias/SETUP_WINDOWS.md) | Retomada rápida no Windows | guias |
| [MCP_TROUBLESHOOTING](guias/MCP_TROUBLESHOOTING.md) | Integração do assistente de IA com o CODESYS | guias |
| [PERGUNTAS_E_RESPOSTAS](academico/PERGUNTAS_E_RESPOSTAS.md) | Perguntas da banca e de curiosos | academico |
| [ROTEIRO_APRESENTACAO](academico/ROTEIRO_APRESENTACAO.md) | Apresentação de 20 min e demonstração de 2 min | academico |
| [ACADEMIC_COMPLIANCE](academico/ACADEMIC_COMPLIANCE.md) | Conformidade com o enunciado da professora | academico |
| [SOURCE_RECONCILIATION](academico/SOURCE_RECONCILIATION.md) | Divergências entre as fontes e decisões (D1–D25) | academico |
| [IMPLEMENTATION_REPORT](projeto/IMPLEMENTATION_REPORT.md) | Requisito → evidência → status | projeto |
| [AUDIT_TESTS_AND_GENERATOR](projeto/AUDIT_TESTS_AND_GENERATOR.md) | Auditoria dos testes e do gerador | projeto |
| [tags.csv](projeto/tags.csv) | As 164 variáveis do programa (tipo, unidade, sentido) | projeto |

## Convenções usadas nos documentos
- **Comprovado** = executado e observado; **compilado** = só compilação; **simulado** = planta/DEMO; **hipótese** = parâmetro não calibrado.
- **DEMO / SIMULADO** = sem CLP; **LÓGICA NO CLP · PLANTA SIMULADA** = Ladder real no CODESYS, com a máquina simulada.
- A interface web **nunca** é parada de emergência: a emergência é hardware independente.
