$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== JARVIS | Compilador Windows ===" -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ não encontrado. Instale Python e habilite o launcher py."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python gerar_icone.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar os ícones." }

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Criei .env.example como .env. Edite-o e insira sua chave Groq antes de executar." -ForegroundColor Yellow
}

& $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name JARVIS --icon "assets\jarvis.ico" --add-data ".env.example;." --collect-all pygame --collect-all edge_tts --hidden-import=pygetwindow --hidden-import=pyautogui --hidden-import=speech_recognition main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller não conseguiu criar o executável." }

Write-Host ""
Write-Host "Build concluído: dist\JARVIS\JARVIS.exe" -ForegroundColor Green
Write-Host "Mantenha o arquivo .env ao lado do executável (dist\JARVIS) com GROQ_API_KEY configurada." -ForegroundColor Yellow
