# JARVIS — Assistente Pessoal

## Preparar o ambiente

1. Instale Python 3.11 ou superior no Windows e habilite o launcher `py`.
2. Copie `.env.example` para `.env` e preencha `GROQ_API_KEY`.
3. Para iniciar a versão Python, execute `INICIAR_JARVIS.bat`.

O inicializador cria `.venv` e instala as dependências listadas em `requirements.txt`.

## Criar o executável Windows

Abra o PowerShell nesta pasta e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

O processo gera o ícone em `assets\jarvis.ico` e o aplicativo em `dist\JARVIS\JARVIS.exe`. A distribuição é no formato `onedir`: mantenha a pasta inteira `dist\JARVIS`, não apenas o EXE. O arquivo `.env` é copiado para essa pasta; mantenha-o privado.

## Criar atalho na área de trabalho

Depois de compilar:

```powershell
.\CRIAR_ATALHO.ps1
```

O script cria o atalho `JARVIS.lnk` na área de trabalho. Para fixá-lo na barra de tarefas, clique com o botão direito no atalho e selecione **Fixar na barra de tarefas** (o Windows pode mostrar primeiro **Mostrar mais opções**).

## Extensão Chrome

Carregue a pasta `jarvis_chrome_extension` em `chrome://extensions` usando **Modo do desenvolvedor** e **Carregar sem compactação**. Revise a permissão de acesso aos sites antes de habilitar o uso global.

## Segurança

- Nunca envie `.env`, chaves de API, tokens ou dados de login ao GitHub.
- A extensão solicita acesso amplo aos sites para cumprir o modo global; habilite somente se confiar no código.
- Páginas internas do Chrome e páginas protegidas não permitem injeção.
- O executável e a extensão ainda precisam de validação no Windows/Chrome antes de serem considerados prontos para uso diário.
