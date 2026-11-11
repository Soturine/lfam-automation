# Runs a CODESYS scripting-API script headless (separate instance). Usage: run-codesys-script.ps1 -Script x.py [-Wait 90]
param([Parameter(Mandatory)][string]$Script, [int]$Wait = 90, [string]$Exe = "D:\ProgramFilesFolder\CODESYS\Common\CODESYS.exe")
$p = Start-Process -FilePath $Exe -ArgumentList '--profile="CODESYS V3.5 SP22 Patch 4"','--noUI',"--runscript=`"$((Resolve-Path $Script).Path)`"" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:LFAM_WORK\run.out" -RedirectStandardError "$env:LFAM_WORK\run.err"
if (-not $p.WaitForExit($Wait * 1000)) { $p.Kill(); "TIMEOUT" } else { "exit $($p.ExitCode)" }
Get-Content "$env:LFAM_WORK\run.out" -ErrorAction SilentlyContinue
