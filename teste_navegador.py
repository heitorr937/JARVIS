
import json
import time
import traceback

from browser_navigator import NavegadorJARVIS


def mostrar_resultado(titulo, resultado):
    print("\n" + "=" * 55)
    print(titulo)
    print("=" * 55)

    if isinstance(resultado, (dict, list)):
        print(json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
            default=str
        ))
    else:
        print(resultado)


def main():
    navegador = NavegadorJARVIS()

    print("=" * 55)
    print("       TESTE DE NAVEGAÇÃO DO JARVIS")
    print("=" * 55)

    try:
        print("\n[1/4] Iniciando a ponte Python...")

        resultado = navegador.iniciar()
        mostrar_resultado("Resultado da inicialização", resultado)

        print("\n[2/4] Verificando a conexão...")
        print("Abra o Chrome e selecione a aba que deseja testar.")
        print("Clique na extensão JARVIS e em 'Ativar nesta aba'.")
        print("\nDepois disso, volte aqui.")

        input("\nPressione ENTER quando tiver ativado a extensão...")

        print("\n[3/4] Aguardando a primeira leitura da página...")
        time.sleep(2)

        estado = navegador.estado()
        mostrar_resultado("ESTADO DO NAVEGADOR", estado)

        print("\n[4/4] Tentando ler a página...")
        pagina = navegador.ler_pagina()

        mostrar_resultado("CONTEÚDO DA PÁGINA", pagina)

        print("\n" + "=" * 55)
        print("TESTE FINALIZADO")
        print("=" * 55)

        print("\nSe o conteúdo da página apareceu acima,")
        print("a comunicação entre Python e Chrome funcionou!")

    except Exception as erro:
        print("\n[ERRO] O teste não conseguiu ser concluído.")
        print("Detalhes:", repr(erro))
        traceback.print_exc()

    finally:
        input("\nPressione ENTER para encerrar o teste...")

        try:
            navegador.parar()
        except Exception:
            try:
                navegador.desconectar()
            except Exception:
                pass

        print("\nPonte Python encerrada.")


if __name__ == "__main__":
    main()
