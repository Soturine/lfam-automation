# Auditoria dos testes e do gerador (2026-11-11)

Gate usado antes de cada push: `pytest -q tests` completo verde (81 testes na última execução) e build headless do CODESYS com 0 erros/0 avisos.

## 1. Testes cujas expectativas mudaram após falharem (e por quê)
| Teste | Mudança | Defeito estava em | Justificativa |
|---|---|---|---|
| `test_no_material_...`, `test_vent_fault_...`, `test_pressure_fault_...` | de "a causa continua ativa" para "a falha fica **travada**" | **teste** | Comportamento correto: ao travar a falha a rosca para e a causa some sozinha; é para isso que o latch existe. Agora a causa é preservada **no Ladder** (`CAUSA_*`, rede 04d) e há testes dedicados |
| `test_pressure_fault_injection...` (5 → 7 MPa) | magnitude da injeção | **cenário** | A 25 rpm a pressão base é 11,75 MPa; +5 MPa não chegava a 17. Não relaxa nenhuma asserção, calibra o cenário |
| Testes que injetavam `EST_PRONTO`/`ENCH_OK`/`INV_RUN`/`PWM_*` | passaram a pré-carregar o temporizador de encharque ou usar `NOPID` | **teste** | Essas variáveis agora são **calculadas** pelas redes e sobrescrevem a injeção; o teste correto cria a condição, não o resultado |
| `test_xml_has_blocks...` | contagem de blocos/TON/PID | **teste** | Reflete o crescimento do programa (PID, CTU, R_TRIG; TON do dente de serra removido) |
| `test_pid_is_reset_when_disabled...` | deixou de ler `eng.integral` | **teste** | O PID saiu do backend e vive no programa |
Nenhum teste foi removido nem teve a tolerância afrouxada para passar.

## 2. Diferenças entre o avaliador Python e o CODESYS (riscos conhecidos)
- **TON:** o avaliador soma `dt` por varredura; o runtime usa tempo real. Equivalem se `dt` = ciclo. Validação online do programa completo **pendente**.
- **PID:** `_PidModel` é um modelo da fórmula documentada do `Util.PID` (anti-windup por limitação). **Não** foi comparado com o runtime; ganhos KP/TN são hipotéticos.
- **Ordem de execução:** o avaliador executa rede a rede de cima para baixo como o CODESYS, mas redes que leem sinais produzidos **mais abaixo** usam o valor do ciclo anterior (documentado em `program.py`).
- **Inicialização:** variável desconhecida vale 0 (como após a carga). Isso mascararia erro de digitação; mitigado por `test_every_identifier_used_in_expressions_is_declared`.
- **REAL_TO_INT / MOD / divisão:** semântica do Python assumida igual à IEC; arredondamento do `.5` não verificado.
- **Comparadores** como contato com expressão e **atribuições** (`:=`) gráficas: compilam, mas o layout não foi revisado visualmente.

## 3. `eval()`
Removido. O avaliador agora é um interpretador de AST com **lista branca** (constantes, nomes, `+ - * / %`, comparações, `not/and/or`, funções fixas); qualquer outra construção levanta erro (`tests/test_expression_safety.py`). As expressões continuam sendo texto fixo do próprio gerador.

## 4. Latches de falha e primeira causa
Antes: a primeira causa era memorizada só no backend (perdia-se se o polling não a visse). Agora: 10 latches `CAUSA_<nome>` no Ladder (rede 04d/04e), setados na varredura em que a falha ainda não estava travada e resetados junto com a falha. Cobertos por testes (primeira causa preservada, causas simultâneas registradas, reset condicionado).

## 5. Entradas inválidas, corrida, reconexão
- Fio aberto: `RAW = 32767` => `TC_Zn_ABERTO` => PID dessa zona em RESET e SSR bloqueado; falha travada.
- Partida a frio com entradas ativas-baixas em 0 => falha (estado seguro).
- Comandos são pulsos; `STOP` é pulso de 1 s (corrigido bug em que o botão ficava preso). Duplo clique é bloqueado na UI (fase "pendente").
- Perda de enlace OPC UA descarta pulsos pendentes e recusa novos comandos; reconexão nunca reenvia comando (`tests/test_opcua_transport.py`).
- **Achado de segurança:** `asyncua` em nível DEBUG imprime a senha da sessão; os loggers são forçados a WARNING e há teste.

## 6. Pendências
Execução online do programa completo no Control Win; comparação PID modelo x runtime; teste de condição de corrida do WebSocket com múltiplos clientes.
