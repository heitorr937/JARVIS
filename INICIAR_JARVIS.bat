@echo off
setlocal
cd /d "%~dp0"
title JARVIS - Inicializador

if not exist ".env" (
  echo.
  echo [ATENCAO] Arquivo .env nao encontrado.
  echo Copie .env.example para .env e preencha GROQ_API_KEY.
  pause
  exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python Launcher nao foi encontrado.
  echo Instale Python 3.11 de 64 bits e habilite o launcher "py".
  pause
  exit /b 1
)

py -3.11 --version >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python 3.11 nao foi encontrado.
  echo Instale Python 3.11 de 64 bits para garantir compatibilidade com PyAudio.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [JARVIS] Criando ambiente isolado com Python 3.11...
  py -3.11 -m venv .venv
  if errorlevel 1 goto erro
)

for /f "usebackq delims=" %%H in (`".venv\Scripts\python.exe" -c "import hashlib;print(hashlib.sha256(open('requirements.txt','rb').read()).hexdigest())"`) do set "REQ_HASH=%%H"
if not defined REQ_HASH (
  echo [ERRO] Nao foi possivel verificar requirements.txt.
  goto erro
)

set "MARCADOR=.venv\requirements.sha256"
set "INSTALLED_HASH="
if exist "%MARCADOR%" set /p INSTALLED_HASH=<"%MARCADOR%"

if not "%REQ_HASH%"=="%INSTALLED_HASH%" (
  echo [JARVIS] Instalando ou atualizando dependencias...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto erro
  ".venv\Scripts\python.exe" -m pip check
  if errorlevel 1 goto erro
  >"%MARCADOR%" echo %REQ_HASH%
) else (
  echo [JARVIS] Dependencias ja estao atualizadas.
)

echo [JARVIS] Iniciando...
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:erro
echo.
echo [ERRO] Nao foi possivel preparar o ambiente do JARVIS.
pause
exit /b 1
