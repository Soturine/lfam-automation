# CP3 - modo PLC (HMI -> FastAPI -> OPC UA -> Ladder no Control Win)

**Status: COMPROVADO em 2026-11-11** (`evidence/CP3_ROUNDTRIP_OK.txt`). Procedimento real, incluindo o que o IDE exigiu, abaixo.
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
6. Num PowerShell, **na pasta do repositório** (`cd` até ela primeiro; o terminal abre em `C:\Users\<voce>`) (senha só na sua sessão, nunca em arquivo):
```powershell
$env:LFAM_MODE="plc"; $env:LFAM_OPCUA_URL="opc.tcp://localhost:4840"
$env:LFAM_OPCUA_USER="SEU_ADMIN"
$sec = Read-Host "senha" -AsSecureString   # -AsSecureString: a senha NAO aparece na tela
$env:LFAM_OPCUA_PASSWORD = [System.Net.NetworkCredential]::new('', $sec).Password
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000
```
7. Em outro terminal: `.\.venv\Scripts\python.exe tools\cp3_roundtrip.py` - imprime cada etapa; termina com `CP3 OK` somente se o **Ladder no Control Win** confirmar.
   Se falhar, a mensagem de `link_error` (em `/api/health`) diz a causa (certificado, usuário, símbolo não publicado...).

## Se o OPC UA não subir nesta máquina
Registre a causa exata (mensagem do runtime). Alternativa B: ponte via Scripting API com o IDE logado (já comprovada no CP2) - ver `CP3_TRANSPORT_ANALYSIS.md`.
Nada disso torna o modo DEMO "CLP": ele continua rotulado `DEMO / SIMULADO`.

## Procedimento que funcionou (ordem real, com os tropeços encontrados)
1. Control Win precisa estar **iniciado** (serviço `CODESYS Control Win V3 - x64` / ícone da bandeja); senão o IDE diz "nenhum dispositivo responde".
2. Online > Logon (admin do dispositivo), Download, Iniciar. O objeto "Servidor OPC UA" não tem tela própria.
3. **Exibição > Tela de segurança > Dispositivos**: gerar certificados de *Servidor OPC UA* e *Comunicação criptografada*. Sem eles o servidor só oferece canal sem criptografia e recusa senha (`BadIdentityTokenInvalid`).
4. **Configuração de símbolos**: marcar `PLC_PRG`, Compilar, e enviar ao CLP (Logon/Download ou Alteração online). Sem isso: "PLC_PRG não encontrado".
5. Cliente: `python tools/gen_opcua_client_cert.py` (cria `work/pki/`, fora do Git) e variável `LFAM_OPCUA_SECURITY="Basic256Sha256,SignAndEncrypt"`. Neste teste a conexão foi aceita sem mover certificado manualmente.
6. O servidor limita operações por pedido (`BadTooManyOperations`): leituras em lotes de 50.
7. Na partida/Download o Ladder trava a falha (entradas em 0 = estado seguro); o roteiro faz o reset do operador antes do teste.
8. Senha: apenas em variável de ambiente da sessão. Ela já apareceu em captura de tela durante o teste: **troque a senha do admin do dispositivo**.
