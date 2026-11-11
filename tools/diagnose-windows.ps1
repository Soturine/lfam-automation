<#
.SYNOPSIS
  Diagnostico local e NAO destrutivo do ambiente LFAM no Windows.
.DESCRIPTION
  Descobre automaticamente CODESYS, Control Win, bridge do MCP e ferramentas de desenvolvimento.
  Nao le senhas, tickets ou arquivos de licenca e nao altera nada. Imprime caminhos locais:
  revise a saida antes de colar em issues ou chats.
  -Redact troca o nome de usuario do Windows por <usuario> na saida.
#>
param(
    [string]$BridgePath,
    [switch]$Redact
)

$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot 'lib-codesys.ps1')
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:fail = 0; $script:warn = 0

function Show([string]$s) { if ($Redact) { $s = $s -replace [regex]::Escape($env:USERNAME), '<usuario>' }; Write-Host $s }
function Ok([string]$m)   { Show ("[ OK ] $m") }
function Warn([string]$m) { $script:warn++; Show ("[AVISO] $m") }
function Bad([string]$m)  { $script:fail++; Show ("[FALHA] $m") }
function Info([string]$m) { Show ("       $m") }

Write-Host '== LFAM / diagnostico do ambiente Windows ==' -ForegroundColor Cyan

# --- Sistema -----------------------------------------------------------------
Write-Host "`n-- Sistema" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
Info ("{0} (build {1}), 64 bits do SO: {2}" -f $os.Caption, $os.BuildNumber, [Environment]::Is64BitOperatingSystem)
if (-not [Environment]::Is64BitOperatingSystem) { Bad 'Windows de 32 bits: o Control Win x64 nao roda.' }
$drive = Get-PSDrive -Name (Split-Path $root -Qualifier).TrimEnd(':')
Info ("Espaco livre na unidade do repositorio: {0:N1} GB" -f ($drive.Free / 1GB))
if ($drive.Free -lt 10GB) { Warn 'Menos de 10 GB livres.' }
$sac = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction SilentlyContinue).VerifiedAndReputablePolicyState
if ($null -ne $sac) {
    $txt = switch ($sac) { 0 {'desligado'} 1 {'ATIVO (pode bloquear DLLs nao assinadas)'} 2 {'avaliacao'} default {"desconhecido ($sac)"} }
    Info "Smart App Control: $txt"
    if ($sac -eq 1) { Warn 'Smart App Control ativo: o bridge do MCP pode ser bloqueado (veja docs/MCP_TROUBLESHOOTING.md).' }
}

# --- Ferramentas de desenvolvimento -------------------------------------------
Write-Host "`n-- Ferramentas" -ForegroundColor Cyan
foreach ($t in @(@('git', $true), @('code', $false), @('claude', $false), @('python', $false), @('node', $false), @('npm', $false))) {
    $c = Get-Command $t[0] -ErrorAction SilentlyContinue
    if ($c) { Ok ("{0}: {1}" -f $t[0], $c.Source) }
    elseif ($t[1]) { Bad ("{0} nao encontrado (obrigatorio)" -f $t[0]) }
    else { Info ("{0}: nao encontrado (opcional, depende do modo de instalacao)" -f $t[0]) }
}
if (Get-Command claude -ErrorAction SilentlyContinue) { Info ("claude --version: {0}" -f ((claude --version) 2>$null)) }

# --- Repositorio -------------------------------------------------------------
Write-Host "`n-- Repositorio" -ForegroundColor Cyan
Info "Raiz: $root"
if (Test-Path -LiteralPath (Join-Path $root 'LFAM_Automacao.project')) { Ok 'LFAM_Automacao.project presente na raiz' } else { Bad 'LFAM_Automacao.project ausente' }
if (Get-Command git -ErrorAction SilentlyContinue) {
    Info ("Branch: {0}" -f (git -C $root branch --show-current))
    $n = @(git -C $root status --short).Count
    Info ("Arquivos alterados/nao rastreados: $n")
}

# --- CODESYS -----------------------------------------------------------------
Write-Host "`n-- CODESYS" -ForegroundColor Cyan
$inst = @(Get-CodesysInstallations)
if ($inst.Count -eq 0) { Bad 'Nenhuma instalacao do CODESYS Development System encontrada.' }
foreach ($i in $inst) {
    Ok ("CODESYS {0} em {1}" -f $i.Version, $i.Root)
    if ($i.Version -notlike '3.5.22.40*') { Warn 'Versao diferente da usada no projeto (3.5.22.40 / SP22 Patch 4).' }
}
if ($inst.Count -gt 1) { Warn 'Varias instalacoes: confirme qual abre o projeto e qual tem o MCP.' }
$running = Get-Process -Name CODESYS -ErrorAction SilentlyContinue
Info ("IDE em execucao: {0}" -f [bool]$running)

# --- Control Win -------------------------------------------------------------
Write-Host "`n-- Control Win e gateway" -ForegroundColor Cyan
$svc = @(Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'CODESYS*' -or $_.DisplayName -like 'CODESYS*' })
if ($svc.Count -eq 0) { Warn 'Nenhum servico CODESYS (Control Win / Gateway) encontrado.' }
foreach ($s in $svc) { Info ("Servico {0}: {1}" -f $s.Name, $s.Status) }
$cw = $svc | Where-Object { $_.Name -like '*Control*' -or $_.DisplayName -like '*Control Win*' } | Select-Object -First 1
if ($cw -and $cw.Status -eq 'Running') { Ok 'Servico do Control Win em execucao (isto NAO prova que a aplicacao esta rodando).' }
elseif ($cw) { Warn 'Servico do Control Win instalado mas parado.' }
$gwPort = Get-NetTCPConnection -LocalPort 1217 -State Listen -ErrorAction SilentlyContinue
Info ("Gateway escutando na porta 1217: {0}" -f [bool]$gwPort)

# --- MCP ---------------------------------------------------------------------
Write-Host "`n-- MCP do CODESYS" -ForegroundColor Cyan
$bridges = @()
if ($BridgePath) { $bridges = @($BridgePath) }
else { foreach ($i in $inst) { $bridges += Find-CodesysMcpBridges -Root $i.Root } }
if ($bridges.Count -eq 0) { Warn 'CodesysMCPBridge.exe nao encontrado (complemento nao instalado?). Modo integrante nao precisa dele.' }
foreach ($b in $bridges) {
    if (-not (Test-Path -LiteralPath $b)) { Bad "Bridge informado nao existe: $b"; continue }
    Ok "Bridge: $b"
    $dir = Split-Path -Parent $b
    foreach ($dll in Get-ChildItem -LiteralPath $dir -Filter '*.dll' -ErrorAction SilentlyContinue | Where-Object Name -like 'ModelContextProtocol*') {
        $sig = Get-AuthenticodeSignature -LiteralPath $dll.FullName
        $blocked = Get-Item -LiteralPath $dll.FullName -Stream Zone.Identifier -ErrorAction SilentlyContinue
        Info ("{0}: assinatura={1}; marca de internet (Zone.Identifier)={2}" -f $dll.Name, $sig.Status, [bool]$blocked)
        if ($blocked) { Warn "$($dll.Name) com marca de bloqueio da internet." }
    }
}
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Info 'claude mcp list (pode demorar alguns segundos):'
    (claude mcp list 2>&1) | Where-Object { $_ -match 'codesys' } | ForEach-Object { Info $_ }
    if (-not ((claude mcp list 2>&1) -match 'codesys-ide')) { Info 'codesys-ide nao registrado neste escopo/pasta.' }
}

Write-Host "`n== Resumo: $script:fail falha(s), $script:warn aviso(s) ==" -ForegroundColor Cyan
Write-Host 'Este script NAO verifica: licencas (use Ferramentas > Gestor de licencas), servidor MCP habilitado no IDE,'
Write-Host 'login no dispositivo, compilacao ou aplicacao em execucao. Veja docs/INSTALLATION_COMPLETE.md (checklist final).'
