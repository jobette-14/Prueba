# Genera el ejecutable ElectroPredict.exe con PyInstaller.
# Uso (desde la raiz del proyecto o desde esta carpeta):
#     powershell -ExecutionPolicy Bypass -File empaquetado\build_exe.ps1

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location $raiz
try {
    Write-Host "Instalando dependencias de escritorio..." -ForegroundColor Cyan
    python -m pip install -r requirements.txt
    python -m pip install "pyinstaller>=6.0"

    Write-Host "Compilando ElectroPredict.exe..." -ForegroundColor Cyan
    python -m PyInstaller --clean --noconfirm empaquetado\electropredict.spec

    $exe = Join-Path $raiz "dist\ElectroPredict.exe"
    if (Test-Path $exe) {
        $mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
        Write-Host "OK: $exe ($mb MB)" -ForegroundColor Green
    } else {
        throw "No se genero el ejecutable."
    }
} finally {
    Pop-Location
}
