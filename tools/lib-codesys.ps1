# Funcoes compartilhadas de descoberta do CODESYS. Uso: . "$PSScriptRoot\lib-codesys.ps1"
# Nada aqui altera o sistema nem le credenciais.

function Get-CodesysInstallations {
    <# Retorna objetos {Exe, Version, Root} encontrados no registro de desinstalacao, em processos em execucao
       e nas pastas padrao de todas as unidades fixas. #>
    $exes = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)

    Get-Process -Name CODESYS -ErrorAction SilentlyContinue | ForEach-Object {
        try { if ($_.Path) { [void]$exes.Add($_.Path) } } catch {}
    }

    $uninstall = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
                   'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
                   'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')
    Get-ItemProperty -Path $uninstall -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -like 'CODESYS*' -and $_.InstallLocation } |
        ForEach-Object {
            $c = Join-Path $_.InstallLocation 'Common\CODESYS.exe'
            if (Test-Path -LiteralPath $c) { [void]$exes.Add($c) }
        }

    $drives = (Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' }).Root
    foreach ($d in $drives) {
        foreach ($rel in @('Program Files\CODESYS*', 'Program Files (x86)\CODESYS*', 'ProgramFilesFolder\CODESYS*', 'CODESYS*')) {
            Get-ChildItem -Path (Join-Path $d $rel) -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $c = Join-Path $_.FullName 'Common\CODESYS.exe'
                if (Test-Path -LiteralPath $c) { [void]$exes.Add($c) }
            }
        }
    }

    foreach ($e in $exes) {
        [pscustomobject]@{
            Exe     = $e
            Version = (Get-Item -LiteralPath $e).VersionInfo.ProductVersion
            Root    = (Split-Path (Split-Path $e -Parent) -Parent)
        }
    }
}

function Find-CodesysMcpBridges {
    param([Parameter(Mandatory)][string]$Root)
    Get-ChildItem -Path $Root -Filter 'CodesysMCPBridge.exe' -Recurse -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName }
}

function Get-DefaultCodesysExe {
    $all = @(Get-CodesysInstallations)
    if ($all.Count -eq 0) { throw 'CODESYS.exe nao encontrado. Informe -Exe ou instale o CODESYS (docs/guias/INSTALLATION_COMPLETE.md).' }
    if ($all.Count -gt 1) { Write-Warning ('Varias instalacoes encontradas; usando a primeira. Use -Exe para escolher. ({0})' -f ($all.Version -join ', ')) }
    $all[0].Exe
}
