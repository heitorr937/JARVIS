import os
import time
import pyautogui
import pyperclip
from dotenv import load_dotenv
from groq import Groq

# Configurações
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
Você é o JARVIS, um assistente de estudos que ajuda um estudante a compreender
e resolver questões escolares.

Analise a questão e responda em português brasileiro, com linguagem simples.

Regras:
- Identifique se é uma questão de alternativas ou dissertativa.
- Explique brevemente o raciocínio, mostrando os passos importantes.
- Destaque claramente a resposta final.
- Em questão de alternativas, informe a letra e o texto da alternativa.
- Em questão dissertativa, escreva uma resposta que o estudante possa revisar.
- Não invente dados que não aparecem no enunciado.
- Se a questão depender de uma figura, gráfico, tabela ou fórmula que não foi
  capturada no texto, explique exatamente qual informação visual está faltando
  e peça uma captura de tela. Não chute uma resposta.
- Não afirme que enviou ou entregou a atividade.
"""

    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": instrucao},
            {"role": "user", "content": "Resolva esta questão:\n\n" + questao}
        ],
        temperature=0.2,
        max_completion_tokens=1200
    )

    return resposta.choices[0].message.content


def main():
    print("=" * 48)
    print("          JARVIS - RESOLVEDOR DE QUESTOES")
    print("=" * 48)

    try:
        questao = capturar_questao()

        if not questao:
            print("\nNão consegui localizar uma questão na página.")
            return

        print("\nQUESTÃO CAPTURADA:")
        print("-" * 48)
        print(questao)
        print("-" * 48)

        print("\nEnviando a questão para a inteligência artificial...")
        resposta = resolver_questao(questao)

        print("\n" + "=" * 48)
        print("                 RESOLUÇÃO DO JARVIS")
        print("=" * 48)
        print(resposta)
        print("=" * 48)

    except Exception as erro:
        print("\nOcorreu um erro:")
        print(erro)

    input("\nPressione ENTER para fechar.")


if __name__ == "__main__":
    main()
