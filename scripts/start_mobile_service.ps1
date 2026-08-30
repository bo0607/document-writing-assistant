$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

Write-Host "Writing service is starting for trusted local networks."
Write-Host "Keep this window open while using the phone app."
& $python "$projectRoot\backend\server.py" --host 0.0.0.0 --port 8000
