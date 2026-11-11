<#
  Roda os testes do projeto.
      powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1           # pytest (Ladder, simulador, backend, OPC UA de teste) + build do SCADA
      powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1 -E2E      # + Playwright (sobe um backend DEMO e o Vite em portas proprias e encerra no fim)
#>
param([switch]$E2E)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$fail = 0

Write-Host "==> pytest" -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pytest -q tests
if ($LASTEXITCODE -ne 0) { $fail++ }

Write-Host "`n==> build do SCADA (tsc + vite)" -ForegroundColor Cyan
Push-Location scada\web
npm run build
if ($LASTEXITCODE -ne 0) { $fail++ }

if ($E2E) {
    Write-Host "`n==> E2E (Playwright)" -ForegroundColor Cyan
    $env:LFAM_MODE = "demo"; $env:LFAM_TIME_SCALE = "30"
    $api = Start-Process -FilePath "..\..\.venv\Scripts\python.exe" -ArgumentList @("-m", "uvicorn", "backend.app:app", "--port", "8100") -WorkingDirectory "..\.." -PassThru -WindowStyle Minimized
    $env:LFAM_API = "127.0.0.1:8100"; $env:LFAM_WEB_PORT = "5180"
    $vite = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev") -PassThru -WindowStyle Minimized
    Start-Sleep 12
    $env:PW_BASE = "http://localhost:5180"
    npx playwright test
    if ($LASTEXITCODE -ne 0) { $fail++ }
    foreach ($p in @($api, $vite)) { if ($p) { & taskkill /PID $p.Id /T /F | Out-Null } }
}
Pop-Location
if ($fail -eq 0) { Write-Host "`nTodos os testes passaram." -ForegroundColor Green } else { Write-Host "`n$fail etapa(s) falharam." -ForegroundColor Red; exit 1 }
