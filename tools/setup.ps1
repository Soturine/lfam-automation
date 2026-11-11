<#
  Prepara o projeto em um PC novo (Windows): ambiente Python (.venv), dependencias do backend e do SCADA.
  Uso (PowerShell aberto na RAIZ do repositorio):
      powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1            # instalacao para rodar o DEMO
      powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1 -Tests     # + navegador do Playwright (testes E2E)
  Nao instala CODESYS (ver docs\guias\INSTALLATION_COMPLETE.md) e nao altera nada fora da pasta do projeto.
#>
param([switch]$Tests)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "ERRO: $m" -ForegroundColor Red; exit 1 }

Step "1/4 Verificando Python (3.10 ou mais novo) e Node (LTS 18+)"
$py = $null
foreach ($c in @("py -3.12", "py -3.11", "py -3.10", "python")) {
    $parts = $c.Split(" ")
    try {
        $v = & $parts[0] $parts[1..($parts.Length - 1)] --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 10) { $py = $c; break }
    } catch { }
}
if (-not $py) { Fail "Python 3.10+ nao encontrado. Instale em https://www.python.org/downloads/ (marque 'Add to PATH') e rode de novo." }
Write-Host "Python: $py"
try { $nv = (node --version) } catch { Fail "Node.js nao encontrado. Instale a versao LTS em https://nodejs.org/ e rode de novo." }
Write-Host "Node: $nv"

Step "2/4 Criando o ambiente Python (.venv) e instalando o backend"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    $parts = $py.Split(" ")
    & $parts[0] $parts[1..($parts.Length - 1)] -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail "Falha ao criar o .venv" }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { Fail "Falha ao instalar as dependencias Python" }

Step "3/4 Instalando o SCADA (npm)"
Push-Location scada\web
if (Test-Path package-lock.json) { npm ci } else { npm install }
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "Falha no npm" }
if ($Tests) { Step "3b/4 Baixando o Chromium do Playwright (testes E2E)"; npx playwright install chromium }
Pop-Location

Step "4/4 Conferindo"
& .\.venv\Scripts\python.exe -c "import fastapi, uvicorn, asyncua; print('backend OK: fastapi', fastapi.__version__)"
Write-Host "`nPronto! Proximo passo:  powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1" -ForegroundColor Green
