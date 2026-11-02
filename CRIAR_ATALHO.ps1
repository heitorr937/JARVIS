$ErrorActionPreference = "Stop"
$Exe = Join-Path $PSScriptRoot "dist\JARVIS\JARVIS.exe"
if (-not (Test-Path $Exe)) {
    throw "Executável não encontrado. Execute build_windows.ps1 primeiro."
}
$Shell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $Shell.CreateShortcut((Join-Path $Desktop "JARVIS.lnk"))
$Shortcut.TargetPath = $Exe
$Shortcut.WorkingDirectory = Split-Path $Exe
$Shortcut.IconLocation = "$Exe,0"
$Shortcut.Description = "Assistente pessoal JARVIS"
$Shortcut.Save()
Write-Host "Atalho JARVIS criado na área de trabalho." -ForegroundColor Green
Write-Host "Para fixar na barra de tarefas: clique com o botão direito no atalho e escolha Mostrar mais opções > Fixar na barra de tarefas."
