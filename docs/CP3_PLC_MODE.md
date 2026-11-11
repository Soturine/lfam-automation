# CP3 - modo PLC (HMI -> FastAPI -> OPC UA -> Ladder no Control Win)

**Status: código e testes do cliente prontos; a prova ponta a ponta no runtime real DEPENDE de uma rodada manual no IDE (abaixo).**
O servidor OPC UA faz parte do Control Win SL (documentação oficial, incl. demo); eu errei antes ao concluir que não existia só por não achar DLLs.

## O que já está verificado (executado)
- `backend/transport.py`: `OpcUaTransport` (cliente asyncua) + `DemoTransport`. 7 testes contra um servidor de **teste** (dublê, nunca usado nos modos reais):
  mapeamento tipado, só escreve entradas/botões/setpoints (nunca saídas do programa), heartbeat parado => dado obsoleto, variáveis ausentes => erro claro,
  queda de enlace descarta pulsos pendentes e recusa comandos, reconexão, e **senha nunca aparece em log** (achado: asyncua em DEBUG imprime a senha; forçado a WARNING).
- Programa `LFAM_PLC.project` (89 elementos, Util, MainTask 100 ms, `PLC_HEARTBEAT`) compilado: **0 erros, 0 avisos**.

## Rodada manual (uns 5 minutos) - só você pode fazer: exige o IDE e o seu administrador do dispositivo
1. No CODESYS abra `work\LFAM_PLC.project` (o `.opt` com gateway/dispositivo já foi copiado).
2. Botão direito em **Application > Adicionar objeto > Communication Manager**; depois botão direito nele > **Adicionar objeto > OPC UA Server**.
3. Botão direito em **Application > Adicionar objeto > Symbol Configuration** (se não houver). Abra-a, **Build** e marque as variáveis de `PLC_PRG`
   (pode marcar todas). Para as entradas (BT_*, SP_*, *_RAW, SEG_OK, MOT_SOBRETEMP, DISJ_AQUEC, SEL_AUTO, ROBO_*, SECADOR_OK, INV_PRONTO, INV_FALHA,
   FUNIL_BAIXO, VENT_OK, K1_CONF, TT_ZSR, TT_RESF, HMI_RESET_LOTES) defina o acesso **Leitura/Escrita**; `PLC_HEARTBEAT` e o resto só Leitura.
4. Segurança (conforme a ajuda oficial): configurações de segurança do dispositivo (OPC UA Server): gerar certificado, `CommunicationMode` = `MIN_SIGNED` ou
   `SIGNED_AND_ENCRYPTED`. **Não habilite acesso anônimo** a menos que você decida conscientemente.
5. Compile, **Online > Login** (seu administrador), baixe a aplicação e **inicie**. No log do runtime/Compilação deve constar o endpoint OPC UA (porta padrão 4840 - confirmar).
6. Num PowerShell, **na pasta do repositório** (senha só na sua sessão, nunca em arquivo):
```powershell
$env:LFAM_MODE="plc"; $env:LFAM_OPCUA_URL="opc.tcp://localhost:4840"
$env:LFAM_OPCUA_USER="SEU_ADMIN"; $env:LFAM_OPCUA_PASSWORD = Read-Host "senha"   # (ou ler de um gerenciador de senhas)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000
```
7. Em outro terminal: `.\.venv\Scripts\python.exe tools\cp3_roundtrip.py` - imprime cada etapa; termina com `CP3 OK` somente se o **Ladder no Control Win** confirmar.
   Se falhar, a mensagem de `link_error` (em `/api/health`) diz a causa (certificado, usuário, símbolo não publicado...).

## Se o OPC UA não subir nesta máquina
Registre a causa exata (mensagem do runtime). Alternativa B: ponte via Scripting API com o IDE logado (já comprovada no CP2) - ver `CP3_TRANSPORT_ANALYSIS.md`.
Nada disso torna o modo DEMO "CLP": ele continua rotulado `DEMO / SIMULADO`.
