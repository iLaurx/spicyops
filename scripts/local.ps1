param([ValidateSet('start','build')][string]$Action='start')
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$taskPython=Join-Path $PWD '.venv/Scripts/python.exe'
if ($Action -eq 'build') { & $taskPython scripts/build_windows.py }
else { & $taskPython run_panel.py }
if ($LASTEXITCODE -ne 0) { throw 'SpicyOps no pudo completar la operación. Revisar el diagnóstico anterior.' }
