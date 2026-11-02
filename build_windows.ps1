$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-PythonStep {
    param(
        [string]$Description,
        [string[]]$Arguments,
        [string]$FailureMessage
    )

    Write-Host "[JARVIS] $Description" -ForegroundColor Cyan
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (código $LASTEXITCODE)."
    }
}

Write-Host "=== JARVIS | Compilador Windows ===" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher não encontrado. Instale Python 3.11 e habilite o launcher py."
}

# PyAudio possui wheels mais previsíveis para Python 3.11 no Windows.
$VersaoPython = & py -3.11 -c "import sys; print(sys.version_info[:2] == (3, 11))" 2>$null
if ($LASTEXITCODE -ne 0 -or $VersaoPython.Trim() -ne "True") {
    throw "Python 3.11 não encontrado. Instale Python 3.11 (64 bits) para compilar o JARVIS."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Não foi possível criar o ambiente virtual." }
}

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Invoke-PythonStep -Description "Atualizando pip..." -Arguments @("-m", "pip", "install", "--upgrade", "pip") -FailureMessage "Falha ao atualizar pip"
Invoke-PythonStep -Description "Instalando dependências..." -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -FailureMessage "Falha ao instalar dependências"
Invoke-PythonStep -Description "Gerando ícones..." -Arguments @("gerar_icone.py") -FailureMessage "Falha ao gerar os ícones"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Criei .env a partir do modelo. Edite-o e insira sua chave Groq antes de executar." -ForegroundColor Yellow
}

Invoke-PythonStep -Description "Compilando o executável..." -Arguments @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
    "--name", "JARVIS", "--icon", "assets\jarvis.ico",
    "--add-data", ".env.example;.",
    "--collect-all", "pygame", "--collect-all", "edge_tts",
    "--hidden-import=pygetwindow", "--hidden-import=pyautogui",
    "--hidden-import=speech_recognition", "--hidden-import=pyaudio",
    "main.py"
) -FailureMessage "PyInstaller não conseguiu criar o executável"

$Destino = Join-Path $PSScriptRoot "dist\JARVIS"
if (-not (Test-Path (Join-Path $Destino "JARVIS.exe"))) {
    throw "O processo terminou sem produzir dist\JARVIS\JARVIS.exe."
}

if (Test-Path ".env") {
    Copy-Item ".env" (Join-Path $Destino ".env") -Force
} else {
    Copy-Item ".env.example" (Join-Path $Destino ".env") -Force
    Write-Host "Configure GROQ_API_KEY em dist\JARVIS\.env antes de iniciar." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Build concluído: dist\JARVIS\JARVIS.exe" -ForegroundColor Green
Write-Host "Distribua a pasta dist\JARVIS inteira, não apenas o EXE." -ForegroundColor Yellow
Write-Host "Nunca compartilhe o arquivo .env." -ForegroundColor Yellow
