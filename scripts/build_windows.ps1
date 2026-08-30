param(
    [switch]$Clean
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$buildRoot = Join-Path $projectRoot "build\windows"
$releaseRoot = Join-Path $projectRoot "release\windows"
$icon = Join-Path $projectRoot "backend\static\icons\app-icon.ico"

if ($Clean) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $releaseRoot -Recurse -Force -ErrorAction SilentlyContinue
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "DocumentWritingAssistant" `
    --icon $icon `
    --add-data "$projectRoot\backend;backend" `
    --collect-all webview `
    --hidden-import webview.platforms.edgechromium `
    --distpath $releaseRoot `
    --workpath $buildRoot `
    --specpath $buildRoot `
    "$projectRoot\desktop_app.py"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output "Build completed: $releaseRoot\DocumentWritingAssistant.exe"
