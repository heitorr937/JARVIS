# JARVIS — Assistente Pessoal

## Preparar o ambiente

1. Para iniciar pelo código, instale Python 3.11 ou superior no Windows e habilite o launcher `py`. Para gerar o executável com `build_windows.ps1`, instale especificamente Python 3.11 (64 bits), por compatibilidade mais previsível com o PyAudio.
2. Copie `.env.example` para `.env` e preencha `GROQ_API_KEY`.
3. Para iniciar a versão Python, siga o procedimento em [`INICIAR_MANUALMENTE.md`](INICIAR_MANUALMENTE.md), que usa comandos digitados no PowerShell e não exige executar o arquivo `.bat` baixado.

O procedimento cria `.venv` e instala as dependências listadas em `requirements.txt`. Na primeira execução, essa etapa pode demorar e exige conexão com a internet. Em computadores com o Controle Inteligente de Aplicativos ativo, scripts baixados como `.bat` e `.ps1` podem ser bloqueados; não desative essa proteção para iniciar o projeto.

## Criar o executável Windows

Abra o PowerShell nesta pasta e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

O processo gera o ícone em `assets\jarvis.ico` e o aplicativo em `dist\JARVIS\JARVIS.exe`. A distribuição é no formato `onedir`: mantenha a pasta inteira `dist\JARVIS`, não apenas o EXE. O arquivo `.env` é copiado para essa pasta; mantenha-o privado. **Atenção:** o executável ainda não possui assinatura digital confiável e pode ser bloqueado pelo Controle Inteligente de Aplicativos. Não desative essa proteção para executá-lo; a distribuição assinada ainda não está implementada.

## Criar atalho na área de trabalho

Depois de compilar:

```powershell
.\CRIAR_ATALHO.ps1
```

O script cria o atalho `JARVIS.lnk` na área de trabalho. Para fixá-lo na barra de tarefas, clique com o botão direito no atalho e selecione **Fixar na barra de tarefas** (o Windows pode mostrar primeiro **Mostrar mais opções**).

## Extensão Chrome

Carregue a pasta `jarvis_chrome_extension` em `chrome://extensions` usando **Modo do desenvolvedor** e **Carregar sem compactação**. Revise a permissão de acesso aos sites antes de habilitar o uso global.

## Autorizar a extensão na ponte local

1. Carregue a extensão em `chrome://extensions` com o modo do desenvolvedor.
2. Copie o **ID** exibido no cartão da extensão JARVIS.
3. No arquivo local `.env`, preencha `JARVIS_EXTENSION_ID=SEU_ID_AQUI`.
4. Reinicie o JARVIS para aplicar a autorização.

O ID é público, mas a comparação exata impede que qualquer extensão Chrome seja aceita automaticamente. Não publique seu arquivo `.env`.

## Navegação web inteligente

A versão de desenvolvimento da navegação usa a extensão Chrome e a ponte local do Python para ler o conteúdo visível da aba ativa e interagir com controles reais da página.

Ações disponíveis nesta etapa:

- Abrir endereços web e navegar entre páginas.
- Pesquisar pelo Google a partir de pedidos em linguagem natural.
- Clicar em links, botões, caixas de seleção, opções e controles acessíveis.
- Preencher campos de texto, pesquisa, e-mail, telefone, número, data e horário.
- Selecionar opções em listas suspensas.
- Rolar páginas e reler o conteúdo após cada ação para decidir o próximo passo.

A extensão não transmite o conteúdo digitado nos campos para a ponte; ela informa apenas se um campo tem conteúdo, se uma caixa está marcada e qual opção está selecionada. Senhas e códigos de autenticação não são preenchidos. Botões de envio/finalização e a tecla Enter permanecem bloqueados nesta etapa.

Teste inicial sugerido depois de instalar esta branch:

`JARVIS, abra o Google e pesquise os melhores mods de Minecraft 1.20.1.`

O JARVIS deve abrir o Google, pesquisar, ler os resultados visíveis e apresentar um resumo. Esta branch ainda precisa de validação integrada no Chrome antes de ser considerada estável.

## Segurança

- Nunca envie `.env`, chaves de API, tokens ou dados de login ao GitHub.
- A extensão solicita acesso amplo aos sites para cumprir o modo global; habilite somente se confiar no código.
- Páginas internas do Chrome e páginas protegidas não permitem injeção.
- O executável e a extensão ainda precisam de validação no Windows/Chrome antes de serem considerados prontos para uso diário.
