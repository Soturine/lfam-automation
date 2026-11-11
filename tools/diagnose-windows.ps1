# Diagnostico local e nao destrutivo do ambiente LFAM no Windows.
param(
    [string]$BridgePath = "D:\ProgramFilesFolder\CODESYS\CODESYS MCP Server\1.1.0.0\CodesysMCPBridge\CodesysMCPBridge.exe"
)

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "== LFAM / Windows diagnostic ==" -ForegroundColor Cyan
Write-Host ("Repositorio: {0}" -f $root)
Write-Host ("Projeto CODESYS: {0}" -f (Test-Path -LiteralPath (Join-Path $root "LFAM_Automacao.project")))

foreach ($name in @("git", "claude", "python", "node", "npm")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Write-Host ("{0}: nao encontrado" -f $name) -ForegroundColor Yellow
    } else {
        Write-Host ("{0}: {1}" -f $name, $cmd.Source)
    }
}

Write-Host ("Bridge existe: {0}" -f (Test-Path -LiteralPath $BridgePath))
if (Test-Path -LiteralPath $BridgePath) {
    Write-Host ("Bridge: {0}" -f $BridgePath)
    $dll = Join-Path (Split-Path -Parent $BridgePath) "ModelContextProtocol.Core.dll"
    Write-Host ("DLL presente: {0}" -f (Test-Path -LiteralPath $dll))
    if (Test-Path -LiteralPath $dll) {
        $signature = Get-AuthenticodeSignature -LiteralPath $dll
        Write-Host ("Assinatura DLL: {0}" -f $signature.Status)
    }
}
Write-Host "Obs.: este script nao verifica licenca, conexao MCP ativa ou execucao do CLP."
Write-Host "Use: claude mcp list; abra o CODESYS para confirmar o servidor e o runtime."

if (Get-Command git -ErrorAction SilentlyContinue) {
    git -C $root status --short
}
