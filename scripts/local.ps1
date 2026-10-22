param([ValidateSet('start','test','build')][string]$Action='start')
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$taskPython=Join-Path $PWD '.venv/Scripts/python.exe'
if ($Action -eq 'test') { & $taskPython manage.py test portal.tests --noinput }
elseif ($Action -eq 'build') { & $taskPython scripts/build_windows.py }
else { & $taskPython run_panel.py }
if ($LASTEXITCODE -ne 0) { throw 'SpicyOps no pudo completar la operación. Revisar el diagnóstico anterior.' }
