# Galeria do SCADA

Todas as imagens são **capturas reais da interface** em modo **DEMO / SIMULADO** (planta simulada). O mesmo visual aparece no modo CLP, com o selo `LÓGICA NO CLP · PLANTA SIMULADA`. Como rodar: [INICIO_RAPIDO](../guias/INICIO_RAPIDO.md).

## Animações
<table>
<tr>
<td align="center" width="50%"><img src="../media/scada-fluxo-completo.gif" alt="Fluxo completo"><br><b>Fluxo completo</b><br><sub>aquecer → encharque → pronto → extrusão → falha de pressão → reset (relógio acelerado)</sub></td>
<td align="center" width="50%"><img src="../media/scada-tour-telas.gif" alt="Tour das telas"><br><b>Tour das 6 telas</b><br><sub>ajuste de setpoint, deposição, receitas, tendência, alarme e histórico</sub></td>
</tr>
<tr>
<td align="center" colspan="2"><img src="../media/scada-celular.gif" alt="No celular" width="240"><br><b>No celular</b> (390 px): mesmo fluxo, layout responsivo</td>
</tr>
</table>

## As 6 telas
| | Tela | O que o operador faz aqui |
|---|---|---|
| <img src="../evidence/scada/tela1_1440x900.png" width="520"> | **01 · Visão geral** | Vê estado, pressão, rotação, temperatura do bico e segurança; **solicita** aquecimento, extrusão, parada e reset. O sinótico mostra a rosca girando e as zonas. O botão só vira *✓ Confirmado* quando o CLP confirma |
| <img src="../evidence/scada/tela2_1440x900.png" width="520"> | **02 · Temperaturas / PID** | Tendência das 5 zonas com limites de 390/400 °C, PV × SP × saída do SSR de cada malha e ajuste de setpoint (bloqueado durante a extrusão) |
| <img src="../evidence/scada/tela3_1440x900.png" width="520"> | **03 · Deposição / IR** | Pressão do fundido, rotação, aquecedor infravermelho e prontidão do robô |
| <img src="../evidence/scada/tela4_1440x900.png" width="520"> | **04 · Alarmes** | Alarmes ativos, **causa que travou a falha**, reset condicionado (só depois que a causa some) e injeção de falhas de teste (DEMO) |
| <img src="../evidence/scada/tela5_1440x900.png" width="520"> | **05 · Receitas** | Conjuntos de setpoints validados contra as faixas permitidas |
| <img src="../evidence/scada/tela6_1440x900.png" width="520"> | **06 · Histórico** | Eventos e comandos, com exportação em CSV |

## Estados que importam
| | |
|---|---|
| <img src="../evidence/scada/estado_nominal_1920x1080_visao_geral.png" width="520"><br>**Operação normal** (1920×1080) | <img src="../evidence/scada/estado_alarme_1440x900_alarmes.png" width="520"><br>**Falha travada** com a causa registrada |
| <img src="../evidence/scada/estado_sem_comunicacao_1440x900_visao_geral.png" width="520"><br>**Sem comunicação**: valores sem cor, comandos desabilitados | <img src="../evidence/scada/tela1_1024x768.png" width="360"><br>**Tablet** (1024×768) |

Também há capturas das 6 telas em 1920×1080, 1440×900, 1024×768 e 390×844 em [`evidence/scada/`](../evidence/scada).

## E o Ladder?
As 15 redes estão em imagens em [LADDER.md](LADDER.md), com a explicação de cada etapa em [LADDER_EXPLICADO.md](LADDER_EXPLICADO.md).
