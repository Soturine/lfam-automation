# Reconciliação de fontes — LFAM

Base: leitura integral de `Arquitetura_Lista_ES_v2.docx`, `Monografia_Automacao_Extrusora.docx` (texto das seções de programa),
`Esquema_Eletrico.docx`, `Seminario_Automacao_Extrusora.pptx`, `Apresentacao_Extrusora_LFAM_com_SCADA.pptx` (texto + notas),
`ENUNCIADO_PROFESSORA.md`, inspeção visual da Prancha Ladder 1 e da tela SCADA 01. As demais pranchas e telas ainda
precisam de inspeção visual (ver "Pendências"). Os originais em `references/` não são versionados nem alterados.

Ordem de decisão: enunciado > fatos da máquina e lista E/S v2 > correções de engenharia testáveis > material gráfico > scripts legados.

## Divergências e decisões

| # | Fonte / local | Problema | Decisão | Teste que valida |
|---|---|---|---|---|
| D1 | Arquitetura/Monografia: S7-1200, OB1, OB30, `PID_Compact`, `%IW/%QW`, `SM0.0` | Não existem no Control Win. `SM0.0` nem é bit nativo do S7 (a própria prancha admite). | Proposta acadêmica continua S7-1200. Demonstração em CODESYS Control Win rotulada "simulação virtual". Semântica reproduzida com tarefa cíclica fixa e FB PID IEC; `SM0.0` vira `TRUE`/ausência de contato. Endereços ficam só em `tags.csv` (coluna acadêmica). | Compilação do projeto + testes de redes |
| D2 | Monografia §9: PIDs em OB30 (100 ms), saída em memória, redes 6/13 liberam SSR | Correto. Ao portar, PID tem de ser chamado **todo ciclo** sem contato antes. | `Task_PID` cíclica 100 ms chama 6 PIDs incondicionalmente; habilitação só na lógica de saída. | Teste: desabilitar zona e ver SSR=0 sem congelar PWM |
| D3 | Prancha 1, rede 4 | SET usa OR (correto, contrariando o aviso do prompt), mas o RESET só testa 6 condições (SEG_OK, MOT, INV_FALHA, SOBRETEMP_400, TC_FAULT, BT_RESET), **sem pressão ≥17, RESF_2M, SEM_MAT, VENT_10S, K1_COL**. Monografia diz que reset exige `M_CAUSA=0` (todas as causas). | Implementar `M_CAUSA` = OR das 10 causas; RESET = `BT_RESET AND NOT M_CAUSA` (e SET com prioridade). Prancha corrigida. | Teste de reset com cada causa ativa (10 casos) |
| D4 | Seminário/Monografia: "dez causas"; Arquitetura: 15 intertravamentos | As 10 causas de `M_CAUSA` são subconjunto dos 15 (os demais são bloqueios, alarmes ou ações específicas). | Matriz intertravamento → ação (falha travada / bloqueio / alarme / desliga IR) em `tags.csv`/docs de redes. | Teste por intertravamento |
| D5 | Pressão: Arquitetura "redução de rotação"; Monografia/Seminário "−10%" na rede 12; prompt cita 17 rpm | Três descrições. Com piso LIMIT 17 rpm, −10% a 18 rpm não reduz. | **Política única:** em `PT ≥ 16,5 MPa`, `REF = LIMIT(17, SP×0,9, 34)`; alarme sempre; `≥ 17 MPa` → falha travada e INV_RUN=0. Limitação (piso 17 rpm) documentada. | Teste: SP 34/20/17 rpm com pressão 16,6 e 17,0 |
| D6 | `INV_REF` (`%QW70`) | Risco de dois escritores (LIMIT e MOVE) | Uma única atribuição final na rede 12. | Verificação estática: 1 escrita por saída |
| D7 | Termopar: Monografia usa 32767 como fio aberto e décimos de grau (3900/4000) | Dependente do módulo SM 1231, não universal em CODESYS | Na simulação o sinal é gerado pelo simulador; fio aberto = flag de qualidade explícita (`TC_Zn_OK`), conversão mantida em 0,1 °C. Documentar como hipótese do módulo. | Teste de fio aberto por zona |
| D8 | Polaridades (Arquitetura) | `SEG_OK=0` falha; `MOT_SOBRETEMP=0` quente; `FUNIL_BAIXO=0` vazio; `BT_DESLIGA=0` parada (NF) | Mantidas no contrato; contatos LD negados conforme tabela. Inicialização: entradas ativas-baixas por padrão em estado seguro (falha) até simulador publicar. | Teste de partida com entradas em 0 |
| D9 | Monografia rede 8: comparadores em série com Z1..Z5 ≥330 | Correto como AND; `M2.0..M2.4` aproximam como 5 flags | Cinco flags explícitos `Zn_ATEMP`, AND no TON de 15 min. | Teste: uma zona cai → TON reinicia |
| D10 | Rede 9 (Monografia): funil fora da condição PRONTO | Coerente com texto; slides listam "dosador com material" no PRONTO (Arquitetura, estado Pronto) | Seguir Monografia (rede 9) e tratar falta de material pelo TON de 60 s (rede 3); registrar a diferença da Arquitetura. | Teste |
| D11 | Slides "com SCADA" | Telas são PNG estáticos com "DADOS SIMULADOS / SEM CONTROLE REAL"; deck tem quebras de layout (a auditar) | Usar como referência visual. Não apresentar como SCADA funcional. | Capturas reais de `evidence/scada` |
| D12 | Esquema elétrico | 220 V trifásico sem neutro, KM3/KM4, cargas — preliminar | Rotulado "ilustrativo / não executivo". A Arquitetura fala em 220 V monofásico no cálculo de K1: **inconsistência de tensão/fases** a resolver com Renan antes de dimensionar. | Revisão do grupo |
| D13 | Estado "Ladder implementa" (Monografia, resumo) | Não comprovado. Seminário diz "Ladder desenhado, ainda não testado no TIA Portal". | Texto acadêmico deve dizer "proposto/representado"; só após testes no CODESYS passa a "implementado". | Atualizar após CP4 |
| D14 | Estado da CPU 1214C: 22 DI / 18 DO e pares reserva | Contas de reserva ok; analógicas sem reserva | Sem mudança; só contexto Siemens | — |
| D15 | Monografia: TT_Z1..Z4 em `%IW96..102`, rede 2 cita `%IW96..%IW104`, TT_ZSR `%IW106`, TT_RESF `%IW108` | Endereços de canal 5/6 só aparecem na rede 3 (1000 em `%IW108`) | Mapa canal→IW em `tags.csv` (96,98,100,102,104,106,108) | Revisão |

## Divergências adicionais (revisão visual das Pranchas 2–4 e do fluxograma, 2026-11-11)

| # | Onde | Observação | Decisão no programa |
|---|---|---|---|
| D16 | Prancha 2, rede 6 (e Prancha 4, rede 13) | Contatos de permissivo ficam **antes** do bloco `PID_Compact`: o bloco só executa com os contatos fechados — o erro que a monografia (§9) descreve. | PID chamado **sem EN** todo ciclo; permissivos vão para `RESET` do PID e para o gate do SSR |
| D17 | Prancha 2, rede 5 | `EST_AQUEC` e `K1_AQUEC` são duas bobinas da mesma rede. | Duas redes (05 e 05b) com **escritor único** por saída |
| D18 | Prancha 2, redes 7 e 8 | Resfriamento e encharque dependem de `EST_AQUEC`. | **Encharque** adotou o gate (sem aquecimento não há PRONTO). **Resfriamento não** (câmara quente > 100 °C é falha por 2 min mesmo com aquecimento desligado) |
| D19 | Prancha 3, rede 9 | `FUNIL_BAIXO` aparece no PRONTO; monografia/rede 3 dizem que não deve (D10). | Mantido D10 (sem funil no PRONTO) |
| D20 | Prancha 3, rede 11 | `TOF` de 5 min sobre `INV_RUN`. | Equivalente com `TON` (rede 11) e teste de religar durante a pós-ventilação |
| D21 | Prancha 3, rede 12 | A linha de pressão faz `MOVE 17 rpm` para `INV_REF`, com dois escritores em `QW70` (a própria prancha avisa). | D5/D6: `LIMIT(17, SP×0,9, 34)`, um escritor |
| D22 | Prancha 4, rede 14 | Carregador exige `EST_AQUEC` e `/FALHA_GERAL`; monografia diz que carrega "inclusive durante uma falha". CTU com `PV = 500`. | Segui a monografia (carrega sempre que o funil esvazia); CTU com `PV = 65535` e reset pelo SCADA |
| D23 | Prancha 4, rede 15 | `ALM_ZSR_BAIXA` só no encharque; amarela apaga em PRONTO; verde exige `/FALHA_GERAL`; sirene inclui `SOBRETEMP_390` e câmara > 100 °C. | **Adotado** (rede 15 e testes) |
| D24 | Fluxograma | Pressão ≥ 16,5 → "alarme e reduzir rotação"; falta de material > 60 s → "falha". Sequência coerente com o programa. A decisão "Parada normal → ventilação 5 min → pronto" está de acordo com a rede 11. | Sem mudança |
| D25 | Prancha 1, rede 3 | `FALHA_SEM_MAT` usa `ALIM_FUNIL` e `EST_EXTRUSAO`; mantido. | Sem mudança |

**Ainda não revisado visualmente:** telas SCADA 02–06 de referência e as imagens embutidas nos DOCX/PPTX (só a tela 01 e as pranchas/fluxograma foram abertos).

## Equivalências Siemens → CODESYS

| Siemens | CODESYS (Control Win) |
|---|---|
| OB1 / OB30 | `PLC_PRG` na `MainTask`; `Task_PID` cíclica 100 ms |
| PID_Compact | FB PID da biblioteca (a escolher/validar) ou FB próprio com anti-windup e PWM |
| NORM_X / SCALE_X | `NORM_X`/`SCALE_X` (Standard/Util) ou aritmética REAL |
| TON/TOF/CTU | Idênticos (IEC 61131-3) |
| SM0.0 | `TRUE` constante |
| PROFINET inversor/robô | Tags simuladas na GVL; sem fieldbus |
| %I/%Q/%M/%IW | Variáveis simbólicas na GVL, sem endereço direto |

## Pendências desta reconciliação
- Inspecionar visualmente Pranchas 2–4, fluxograma, SCADA 02–06 e imagens embutidas nos DOCX/PPTX.
- Revisar slides do deck com SCADA (quebras/sobreposição) renderizando páginas.
- Confirmar tensão do sistema e cargas com a área elétrica.
