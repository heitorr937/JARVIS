import os
import re
import time
import pyautogui
import pyperclip
from dotenv import load_dotenv
from groq import Groq

# Carrega a chave do arquivo .env que fica na mesma pasta deste script
PASTA = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PASTA, ".env"))
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    print("ERRO: não encontrei GROQ_API_KEY no arquivo .env.")
    input("\nPressione ENTER para fechar.")
    raise SystemExit

client = Groq(api_key=API_KEY, timeout=60.0, max_retries=0)
MODELO = "openai/gpt-oss-20b"


def capturar_questao():
    print("\nDeixe uma questão aberta no Geekie One.")
    print("Quando a contagem começar, clique na página da questão.")
    for segundos in range(10, 0, -1):
        print(f"Captura em {segundos}...")
        time.sleep(1)

    pyperclip.copy("")
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(1)

    texto = pyperclip.paste()
    inicio = texto.find("Atividade - Questão")
    if inicio == -1:
        inicio = texto.find("Questão 01")
    if inicio == -1:
        inicio = texto.find("Questão")

    if inicio == -1:
        return ""

    questao = texto[inicio:]
    marcadores_fim = [
        "Traduzir para Libras",
        "Mais Acessibilidade",
        "Sintetizar para Voz"
    ]
    finais = [questao.find(m) for m in marcadores_fim if questao.find(m) != -1]
    if finais:
        questao = questao[:min(finais)]
    return questao.strip()


def resolver_questao(questao):
    instrucao = """
Você é o JARVIS, um assistente de estudos. Resolva a questão em português
brasileiro, com linguagem simples e explicação curta.

Se a questão depender de figura, gráfico, tabela ou fórmula que não esteja
visível no texto, NÃO chute: explique que é necessária uma captura de tela.

Ao final, inclua exatamente este bloco:
[RESPOSTA_PARA_PREENCHER]
Aqui coloque somente a resposta que deve ser inserida no campo do Geekie.
[/RESPOSTA_PARA_PREENCHER]

Para questões dissertativas, escreva uma resposta completa e adequada ao campo.
Para múltipla escolha, informe somente a letra e o texto da alternativa nesse bloco.
Não diga que entregou a atividade.
"""
    resultado = client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": instrucao},
            {"role": "user", "content": "Resolva esta questão:\n\n" + questao}
        ],
        temperature=0.2,
        max_completion_tokens=1200
    )
    return resultado.choices[0].message.content or ""


def extrair_resposta(resposta_completa):
    inicio = resposta_completa.find("[RESPOSTA_PARA_PREENCHER]")
    fim = resposta_completa.find("[/RESPOSTA_PARA_PREENCHER]")
    if inicio == -1 or fim == -1 or fim <= inicio:
        return ""
    inicio += len("[RESPOSTA_PARA_PREENCHER]")
    return resposta_completa[inicio:fim].strip()


def main():
    print("=" * 52)
    print("       JARVIS - RESOLVER E PREENCHER (TESTE)")
    print("=" * 52)
    print("Este teste NÃO entrega nem finaliza a atividade.")

    try:
        questao = capturar_questao()
        if not questao:
            print("\nNão consegui localizar uma questão na página.")
            return

        print("\nQUESTÃO CAPTURADA:")
        print("-" * 52)
        print(questao)
        print("-" * 52)

        print("\nEnviando para a inteligência artificial...")
        resposta_completa = resolver_questao(questao)
        resposta_preencher = extrair_resposta(resposta_completa)

        print("\nRESOLUÇÃO DO JARVIS:")
        print("=" * 52)
        print(resposta_completa)
        print("=" * 52)

        if not resposta_preencher:
            print("\nNão consegui separar a resposta para preenchimento.")
            return

        print("\nSomente este conteúdo será copiado para o Geekie:")
        print("-" * 52)
        print(resposta_preencher)
        print("-" * 52)

        if re.search(r"Alternativa|A\)|B\)|C\)|D\)", questao, re.IGNORECASE):
            print("\nEsta parece ser uma questão de alternativas.")
            print("Nesta etapa, o JARVIS ainda NÃO seleciona alternativas.")
            print("Vamos testar primeiro o preenchimento de questões dissertativas.")
            return

        confirmar = input(
            "\nDeseja colar essa resposta no campo dissertativo? (S/N): "
        ).strip().lower()

        if confirmar != "s":
            print("\nTudo bem. Nenhum texto foi inserido.")
            return

        print("\nEm 8 segundos, clique dentro do campo 'Sua resposta' no Chrome.")
        print("Não clique em Entregar.")
        for segundos in range(8, 0, -1):
            print(f"{segundos}...")
            time.sleep(1)

        pyperclip.copy(resposta_preencher)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        print("\nTexto colado no campo. Confira no navegador.")
        print("O JARVIS NÃO clicou em Entregar.")

    except Exception as erro:
        print("\nOcorreu um erro:")
        print(erro)

    input("\nPressione ENTER para fechar.")


if __name__ == "__main__":
    main()
