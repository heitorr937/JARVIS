"""Diagnóstico local do JARVIS (não envia chaves nem dados para a internet)."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import socket
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORTA = 8765
URL_HEALTH = f"http://{HOST}:{PORTA}/health"

DEPENDENCIAS = {
    "groq": "groq",
    "python-dotenv": "dotenv",
    "SpeechRecognition": "speech_recognition",
    "edge-tts": "edge_tts",
    "pygame": "pygame",
    "PyAutoGUI": "pyautogui",
    "pyperclip": "pyperclip",
    "PyGetWindow": "pygetwindow",
    "Pillow": "PIL",
    "PyAudio": "pyaudio",
}


def carregar_env():
    caminho = ROOT / ".env"
    valores = {}

    if not caminho.is_file():
        return valores, caminho

    try:
        from dotenv import dotenv_values
        valores = {
            chave: valor
            for chave, valor in dotenv_values(caminho).items()
            if valor is not None
        }
    except Exception:
        # Leitura simples de contingência; nunca imprime os valores.
        for linha in caminho.read_text(encoding="utf-8-sig").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip().strip("\"'")

    return valores, caminho


def resultado(status, titulo, detalhe=""):
    simbolo = {"OK": "[OK]", "AVISO": "[AVISO]", "ERRO": "[ERRO]"}[status]
    print(f"{simbolo} {titulo}")
    if detalhe:
        print(f"     {detalhe}")


def verificar_ponte():
    try:
        with urlopen(URL_HEALTH, timeout=2) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
            if resposta.status == 200 and corpo.get("ok") is True:
                resultado("OK", "Ponte Python ativa", URL_HEALTH)
                return True
            resultado("AVISO", "Resposta inesperada da porta 8765", str(corpo)[:180])
            return False
    except URLError as erro:
        motivo = getattr(erro, "reason", erro)
        if isinstance(motivo, ConnectionRefusedError):
            resultado(
                "ERRO",
                "Nenhum serviço aceitou conexão na porta 8765",
                "Inicie o JARVIS e confira se browser_navigator.iniciar() foi executado."
            )
        else:
            resultado("ERRO", "Falha ao consultar a ponte local", str(motivo))
        return False
    except TimeoutError:
        resultado("ERRO", "A ponte local não respondeu em 2 segundos")
        return False
    except Exception as erro:
        resultado("ERRO", "Não foi possível validar a ponte", f"{type(erro).__name__}: {erro}")
        return False


def main():
    print("=" * 62)
    print("DIAGNÓSTICO LOCAL DO JARVIS")
    print("Nenhuma chave, senha ou conteúdo de página será exibido.")
    print("=" * 62)

    erros = 0
    avisos = 0

    versao = sys.version_info
    if versao >= (3, 11):
        resultado("OK", "Versão do Python", sys.version.split()[0])
    else:
        resultado("ERRO", "Python incompatível", "Use Python 3.11 ou superior.")
        erros += 1

    env, caminho_env = carregar_env()
    if caminho_env.is_file():
        resultado("OK", "Arquivo .env encontrado")
    else:
        resultado("ERRO", "Arquivo .env não encontrado", "Copie .env.example para .env.")
        erros += 1

    groq_key = os.getenv("GROQ_API_KEY") or env.get("GROQ_API_KEY", "")
    if groq_key.strip() and "SUA_CHAVE" not in groq_key.upper():
        resultado("OK", "GROQ_API_KEY configurada", "O valor foi ocultado.")
    else:
        resultado("ERRO", "GROQ_API_KEY ausente ou não configurada")
        erros += 1

    extension_id = os.getenv("JARVIS_EXTENSION_ID") or env.get("JARVIS_EXTENSION_ID", "")
    if re.fullmatch(r"[a-p]{32}", extension_id.strip()):
        resultado("OK", "ID da extensão configurado", "O ID foi ocultado.")
    elif extension_id.strip():
        resultado("ERRO", "ID da extensão tem formato inválido", "O valor foi ocultado.")
        erros += 1
    else:
        resultado("ERRO", "JARVIS_EXTENSION_ID não configurado")
        erros += 1

    gitignore = ROOT / ".gitignore"
    if gitignore.is_file() and ".env" in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
        resultado("OK", ".env protegido pelo .gitignore")
    else:
        resultado("AVISO", "Confira se .env está protegido pelo .gitignore")
        avisos += 1

    for pacote, modulo in DEPENDENCIAS.items():
        try:
            presente = importlib.util.find_spec(modulo) is not None
        except (ImportError, ValueError):
            presente = False
        if presente:
            resultado("OK", f"Dependência encontrada: {pacote}")
        elif pacote == "PyAudio":
            resultado("AVISO", "PyAudio não encontrado", "O reconhecimento pelo microfone pode não funcionar.")
            avisos += 1
        else:
            resultado("ERRO", f"Dependência ausente: {pacote}")
            erros += 1

    manifest_path = ROOT / "jarvis_chrome_extension" / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            permissoes = manifest.get("host_permissions", [])
            if (
                manifest.get("manifest_version") == 3
                and "http://127.0.0.1:8765/*" in permissoes
            ):
                resultado(
                    "OK",
                    "Manifest da extensão válido",
                    f"Versão {manifest.get('version', 'desconhecida')}."
                )
            else:
                resultado("ERRO", "Manifest sem configuração esperada da ponte")
                erros += 1
        except Exception as erro:
            resultado("ERRO", "Não foi possível ler manifest.json", str(erro))
            erros += 1
    else:
        resultado("ERRO", "Pasta da extensão Chrome não encontrada")
        erros += 1

    for arquivo in ("main.py", "browser_navigator.py", "activity_parser.py", "activity_tutor.py"):
        if (ROOT / arquivo).is_file():
            resultado("OK", f"Arquivo encontrado: {arquivo}")
        else:
            resultado("ERRO", f"Arquivo ausente: {arquivo}")
            erros += 1

    if not verificar_ponte():
        erros += 1

    print("-" * 62)
    print(f"Resultado: {erros} erro(s), {avisos} aviso(s).")
    if erros:
        print("Corrija os itens marcados como [ERRO] e execute o diagnóstico novamente.")
        return 1
    print("Verificações locais concluídas. Ainda é necessário testar a extensão no Chrome real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
