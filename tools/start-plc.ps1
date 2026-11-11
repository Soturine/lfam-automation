<#
  Sobe o backend em modo PLC (Ladder rodando no CODESYS Control Win via OPC UA criptografado).
  A senha e pedida de forma OCULTA e fica somente na memoria desta sessao: nao e gravada em arquivo nem registrada.
  Pre-requisitos: docs\guias\MODO_PLC.md (Control Win iniciado, OPC UA/certificados/simbolos configurados e aplicacao em execucao).
  Uso (PowerShell na RAIZ do repositorio):
      powershell -ExecutionPolicy Bypass -File .\tools\start-plc.ps1 -User admin
      powershell -ExecutionPolicy Bypass -File .\tools\start-plc.ps1 -User admin -Url opc.tcp://localhost:4840 -Web
  Com -Web tambem sobe o SCADA (Vite) apontando para este backend.
#>
param([Parameter(Mandatory)][string]$User, [string]$Url = "opc.tcp://localhost:4840", [int]$ApiPort = 8000, [switch]$Web)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { Write-Host "Rode antes: tools\setup.ps1" -ForegroundColor Red; exit 1 }

# certificado de cliente local (autoassinado, fora do Git); gerado uma unica vez
if (-not (Test-Path ".\work\pki\client_cert.der")) {
    Write-Host "Gerando certificado de cliente OPC UA em work\pki (uma vez)..."
    & .\.venv\Scripts\python.exe tools\gen_opcua_client_cert.py
}

$sec = Read-Host "Senha do usuario '$User' do dispositivo CODESYS" -AsSecureString
$env:LFAM_MODE = "plc"; $env:LFAM_OPCUA_URL = $Url; $env:LFAM_OPCUA_USER = $User
$env:LFAM_OPCUA_SECURITY = "Basic256Sha256,SignAndEncrypt"
$env:LFAM_OPCUA_PASSWORD = [System.Net.NetworkCredential]::new('', $sec).Password

if ($Web) {
    $env:LFAM_API = "127.0.0.1:$ApiPort"
    Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev") -WorkingDirectory ".\scada\web" -WindowStyle Minimized
    Write-Host "SCADA em http://localhost:5173 (selo: LOGICA NO CLP / PLANTA SIMULADA)"
}
Write-Host "Backend PLC em http://127.0.0.1:$ApiPort  (Ctrl+C encerra). Em /api/health, 'link_error' diz a causa se nao conectar."
& .\.venv\Scripts\python.exe -m uvicorn backend.app:app --port $ApiPort
