# Iniciar o JARVIS sem executar arquivos .bat ou .ps1

Em alguns computadores com Windows 11, o Controle Inteligente de Aplicativos bloqueia scripts baixados da internet, incluindo arquivos de lote. Não desative essa proteção para iniciar o JARVIS.

Este procedimento usa o Python instalado para preparar e iniciar o código-fonte manualmente, a partir de comandos digitados no PowerShell. Não execute o `.bat` nem o `.ps1` baixados.

## 1. Requisitos

- Python 3.11 de 64 bits instalado e disponível pelo comando `py`.
- A pasta do projeto JARVIS extraída em um local conhecido.
- Arquivo local `.env` configurado com `GROQ_API_KEY`.

Não compartilhe o arquivo `.env` nem copie sua chave para comandos, capturas de tela ou mensagens.

## 2. Abrir o PowerShell na pasta do projeto

No Explorador de Arquivos, abra a pasta do JARVIS. Clique na barra de endereço, digite `powershell` e pressione Enter. Isso abre o PowerShell já nessa pasta.

## 3. Conferir o Python

Digite:

```powershell
py -3.11 --version
```

O resultado deve indicar Python 3.11.x. Se o comando não for reconhecido, pare aqui e instale Python 3.11 de 64 bits pelo site oficial do Python.

## 4. Preparar o ambiente isolado

Digite estes comandos, um por vez:

```powershell
py -3.11 -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```powershell
.\.venv\Scripts\python.exe -m pip check
```

A instalação exige internet e pode demorar na primeira vez. Se aparecer erro, pare e copie o texto do erro (sem incluir chaves ou dados privados).

Se a pasta `.venv` já existir, não é necessário recriá-la; execute os comandos de instalação e verificação.

## 5. Iniciar

Quando as dependências estiverem instaladas e o `.env` estiver configurado, digite:

```powershell
.\.venv\Scripts\pythonw.exe main.py
```

O JARVIS deve abrir sem a janela do console. Se não abrir, use este comando para exibir o erro no próprio PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Observação sobre o executável

O executável gerado localmente pelo PyInstaller ainda não tem assinatura digital de um certificado confiável. O Controle Inteligente de Aplicativos pode bloqueá-lo. Não desligue a proteção para forçar a execução. Uma distribuição executável confiável exigiria um processo de assinatura digital adequado e validação posterior.
