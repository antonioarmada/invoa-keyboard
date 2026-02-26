param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt pyinstaller

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name TecladoOcular `
    --distpath dist-windows `
    --workpath build/pyinstaller-windows `
    --specpath build/pyinstaller-spec `
    main.py

Write-Host "Build listo: dist-windows/TecladoOcular/TecladoOcular.exe"
