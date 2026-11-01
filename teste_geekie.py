
import time
import webbrowser

URL_GEEKIE = "https://one.geekie.com.br/"

print("JARVIS: iniciando integração com o Geekie One...")
print("JARVIS: abrindo o navegador padrão...")

try:
    webbrowser.open(URL_GEEKIE, new=2)

    time.sleep(3)

    print("\nJARVIS: Geekie One aberto!")
    print("Se necessário, entre na sua conta manualmente.")
    print("Não informe sua senha ao JARVIS.")

except Exception as erro:
    print(f"\nJARVIS: não foi possível abrir o Geekie.")
    print(f"Detalhes: {erro}")

input("\nPressione ENTER para fechar...")
