
import time
import re
import pyautogui
import pyperclip

print("JARVIS - LEITOR DE QUESTOES")
print("Deixe uma questão aberta no Geekie One.")
print("Clique na página quando começar a contagem.")

for segundos in range(10, 0, -1):
    print(f"Começando em {segundos}...")
    time.sleep(1)

try:
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
        print("Não encontrei uma questão nesta página.")
    else:
        questao = texto[inicio:]

        fim = questao.find("Traduzir para Libras")

        if fim != -1:
            questao = questao[:fim]

        print("\n========== QUESTAO IDENTIFICADA ==========")
        print(questao.strip())
        print("==========================================")

        if re.search(r"Alternativa", questao, re.IGNORECASE):
            print("\nTipo identificado: ALTERNATIVAS")
        elif re.search(r"Dissertativa", questao, re.IGNORECASE):
            print("\nTipo identificado: DISSERTATIVA")
        else:
            print("\nTipo ainda não identificado.")

except Exception as erro:
    print("Erro:", erro)

input("\nPressione ENTER para fechar.")
