@echo off
setlocal
cd /d "%~dp0"
title JARVIS - Inicializador
where py >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao foi encontrado.
  echo Instale Python 3.11 ou superior e marque "Add Python to PATH".
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [JARVIS] Criando ambiente isolado...
  py -3 -m venv .venv
  if errorlevel 1 goto erro
)
echo [JARVIS] Atualizando ferramentas...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
echo [JARVIS] Conferindo dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
if not exist ".env" (
  echo.
  echo [ATENCAO] Arquivo .env nao encontrado.
  echo Crie .env com a linha: GROQ_API_KEY=sua_chave
  pause
  exit /b 1
)
echo [JARVIS] Iniciando...
".venv\Scripts\pythonw.exe" main.py
exit /b 0
:erro
echo.
echo [ERRO] Nao foi possivel preparar o ambiente.
pause
exit /b 1
