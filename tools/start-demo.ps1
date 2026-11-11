<#
  Sobe o SCADA em modo DEMO (planta simulada; nao precisa de CODESYS) e abre o navegador.
  Uso (PowerShell na RAIZ do repositorio, depois de rodar tools\setup.ps1):
      powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1            # relogio 30x (encharque de 15 min em ~30 s)
      powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1 -Scale 1   # tempo real
      powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1 -Stop      # encerra backend e frontend
#>
param([int]$Scale = 30, [int]$ApiPort = 8000, [int]$WebPort = 5173, [switch]$Stop, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function PidsOnPort($p) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique }

if ($Stop) {
    foreach ($p in @($ApiPort, $WebPort)) { foreach ($id in (PidsOnPort $p)) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; Write-Host "encerrado PID $id (porta $p)" } }
    return
}
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { Write-Host "Rode antes: powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1" -ForegroundColor Red; exit 1 }
if (-not (Test-Path ".\scada\web\node_modules")) { Write-Host "SCADA sem dependencias. Rode: tools\setup.ps1" -ForegroundColor Red; exit 1 }
foreach ($p in @($ApiPort, $WebPort)) { if (PidsOnPort $p) { Write-Host "A porta $p ja esta em uso. Encerre com: tools\start-demo.ps1 -Stop (ou use -ApiPort/-WebPort)" -ForegroundColor Red; exit 1 } }

$env:LFAM_MODE = "demo"; $env:LFAM_TIME_SCALE = "$Scale"
Write-Host "Backend DEMO (relogio ${Scale}x) em http://127.0.0.1:$ApiPort ..."
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList @("-m", "uvicorn", "backend.app:app", "--port", "$ApiPort") -WindowStyle Minimized

$env:LFAM_API = "127.0.0.1:$ApiPort"; $env:LFAM_WEB_PORT = "$WebPort"
Write-Host "SCADA (Vite) em http://localhost:$WebPort ..."
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev") -WorkingDirectory ".\scada\web" -WindowStyle Minimized

$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 750
    try {
        $h = Invoke-RestMethod "http://127.0.0.1:$ApiPort/api/health" -TimeoutSec 2
        $w = Invoke-WebRequest "http://localhost:$WebPort/" -UseBasicParsing -TimeoutSec 2
        if ($h.status -eq "ok" -and $w.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
}
if (-not $ok) { Write-Host "Nao subiu a tempo. Veja as janelas minimizadas (backend e Vite) para a mensagem de erro." -ForegroundColor Red; exit 1 }
Write-Host "`nOK! Abra http://localhost:$WebPort  (selo DEMO / SIMULADO no canto da tela)." -ForegroundColor Green
Write-Host "Roteiro: Ligar aquecimento -> aguardar PRONTO -> Iniciar extrusao -> aba Alarmes -> injetar falha -> Reset."
Write-Host "Para encerrar: powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1 -Stop"
if (-not $NoBrowser) { Start-Process "http://localhost:$WebPort" }
