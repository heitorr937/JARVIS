
from __future__ import annotations

import json
import os
import re
import time
import uuid
from threading import Lock, Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from typing import Any


HOST = "127.0.0.1"
PORTA = 8765


class ErroNavegadorJARVIS(Exception):
    pass


class NavegadorJARVIS:

    def __init__(self, host=HOST, porta=PORTA):
        self.host = host
        self.porta = int(porta)

        self._servidor = None
        self._thread = None

        self._snapshot = None
        self._extensao_status = {
            "ativo": False,
            "ultima_atualizacao": 0,
            "aba": None
        }
        self._comandos = []
        self._resultados = {}

        self._lock = Lock()

    @property
    def conectado(self):
        return self._servidor is not None

    @property
    def endereco(self):
        return f"http://{self.host}:{self.porta}"

    def iniciar(self):
        if self.conectado:
            return {
                "status": "servidor iniciado",
                "endereco": self.endereco
            }

        navegador = self

        class Handler(BaseHTTPRequestHandler):

            def log_message(self, *_args):
                pass

            def responder(self, codigo=200, dados=None):
                corpo = json.dumps(
                    dados or {},
                    ensure_ascii=False
                ).encode("utf-8")

                self.send_response(codigo)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                origem = self.headers.get("Origin")
                if origem and self.origem_permitida():
                    self.send_header("Access-Control-Allow-Origin", origem)
                    self.send_header("Vary", "Origin")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def origem_permitida(self):
                # Bloqueia páginas web comuns e tentativas simples de DNS rebinding.
                # O cliente Python local não envia Origin.
                origem = self.headers.get("Origin")
                host = self.headers.get("Host", "")
                host_permitido = {
                    f"{navegador.host}:{navegador.porta}",
                    f"127.0.0.1:{navegador.porta}",
                    f"localhost:{navegador.porta}"
                }
                if host not in host_permitido:
                    return False
                if origem is None:
                    return True
                extensao_id = os.getenv("JARVIS_EXTENSION_ID", "").strip()
                origem_esperada = "chrome-extension://" + extensao_id if extensao_id else ""
                return bool(origem_esperada and origem == origem_esperada)

            def do_OPTIONS(self):
                if not self.origem_permitida():
                    self.responder(403, {
                        "ok": False,
                        "erro": "Origem não autorizada."
                    })
                    return

                self.send_response(204)
                origem = self.headers.get("Origin")
                if origem:
                    self.send_header("Access-Control-Allow-Origin", origem)
                    self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                if not self.origem_permitida():
                    self.responder(403, {
                        "ok": False,
                        "erro": "Origem não autorizada."
                    })
                    return

                caminho = urlparse(self.path).path

                if caminho == "/health":
                    self.responder(200, {
                        "ok": True,
                        "servico": "JARVIS"
                    })

                elif caminho == "/snapshot":
                    with navegador._lock:
                        snapshot = navegador._snapshot

                    self.responder(200, {
                        "ok": True,
                        "snapshot": snapshot
                    })

                elif caminho == "/extension/status":
                    with navegador._lock:
                        estado = dict(navegador._extensao_status)

                    self.responder(200, {
                        "ok": True,
                        "extensao": estado
                    })

                elif caminho == "/next":
                    from urllib.parse import parse_qs
                    parametros = parse_qs(urlparse(self.path).query)
                    aba_id = parametros.get("tab_id", [None])[0]
                    with navegador._lock:
                        # Descarta comandos vencidos antes de entregá-los ao Chrome.
                        agora = time.time()
                        navegador._comandos = [
                            item for item in navegador._comandos
                            if float(item.get("_expira_em", 0)) > agora
                        ]
                        comando = None
                        if navegador._comandos:
                            primeiro = navegador._comandos[0]
                            destino = primeiro.get("_aba_id")
                            if destino is None or str(destino) == str(aba_id):
                                comando = navegador._comandos.pop(0)

                    self.responder(200, {
                        "ok": True,
                        "comando": comando
                    })

                else:
                    self.responder(404, {
                        "ok": False,
                        "erro": "Rota não encontrada."
                    })

            def do_POST(self):
                if not self.origem_permitida():
                    self.responder(403, {
                        "ok": False,
                        "erro": "Origem não autorizada."
                    })
                    return

                caminho = urlparse(self.path).path

                tamanho = int(
                    self.headers.get("Content-Length", "0")
                )

                try:
                    dados = json.loads(
                        self.rfile.read(tamanho).decode("utf-8") or "{}"
                    )
                except Exception:
                    self.responder(400, {
                        "ok": False,
                        "erro": "JSON inválido."
                    })
                    return

                if caminho == "/snapshot":
                    with navegador._lock:
                        navegador._snapshot = dados

                    self.responder(200, {"ok": True})

                elif caminho == "/extension/status":
                    with navegador._lock:
                        navegador._extensao_status = {
                            "ativo": bool(dados.get("ativo")),
                            "ultima_atualizacao": time.time(),
                            "aba": {
                                "titulo": str(dados.get("titulo", ""))[:200],
                                "url": str(dados.get("url", ""))[:1000]
                            }
                        }

                    self.responder(200, {"ok": True})

                elif caminho == "/resultado":
                    identificador = dados.get("id")

                    if identificador:
                        with navegador._lock:
                            navegador._resultados[identificador] = dados

                    self.responder(200, {"ok": True})

                else:
                    self.responder(404, {
                        "ok": False,
                        "erro": "Rota não encontrada."
                    })

        try:
            self._servidor = ThreadingHTTPServer(
                (self.host, self.porta),
                Handler
            )

            self._servidor.daemon_threads = True

            self._thread = Thread(
                target=self._servidor.serve_forever,
                daemon=True
            )

            self._thread.start()

            return {
                "status": "servidor iniciado",
                "endereco": self.endereco
            }

        except OSError as erro:
            self._servidor = None

            raise ErroNavegadorJARVIS(
                f"Não consegui iniciar a ponte na porta "
                f"{self.porta}: {erro}"
            ) from erro

    def parar(self):
        if self._servidor:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._servidor = None

        self._thread = None

    def desconectar(self):
        self.parar()

    def _exigir_servidor(self):
        if not self.conectado:
            raise ErroNavegadorJARVIS(
                "A ponte Python não está iniciada. "
                "Execute iniciar() primeiro."
            )

    def _requisicao(self, caminho, dados=None):
        import urllib.request

        endereco = self.endereco + caminho

        if dados is None:
            requisicao = urllib.request.Request(
                endereco,
                method="GET"
            )
        else:
            corpo = json.dumps(
                dados,
                ensure_ascii=False
            ).encode("utf-8")

            requisicao = urllib.request.Request(
                endereco,
                data=corpo,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

        with urllib.request.urlopen(
            requisicao,
            timeout=5
        ) as resposta:
            return json.loads(resposta.read().decode("utf-8"))

    def _obter_snapshot(self):
        self._exigir_servidor()

        try:
            resposta = self._requisicao("/snapshot")
            snapshot = resposta.get("snapshot")

            if not snapshot:
                raise ErroNavegadorJARVIS(
                    "Ainda não recebi dados da extensão. "
                    "Ative o JARVIS na aba do Chrome."
                )

            return snapshot

        except ErroNavegadorJARVIS:
            raise

        except Exception as erro:
            raise ErroNavegadorJARVIS(
                f"Erro ao consultar a extensão: {erro}"
            ) from erro

    def _enviar_comando(self, acao, timeout=10):
        self._exigir_servidor()

        identificador = uuid.uuid4().hex

        comando = {
            "id": identificador,
            **acao,
            "_expira_em": time.time() + max(1, float(timeout))
        }

        with self._lock:
            self._resultados.pop(identificador, None)
            snapshot = self._snapshot or {}
            aba_id = snapshot.get("_jarvis_tab_id")
            if aba_id is None:
                raise ErroNavegadorJARVIS(
                    "Ainda não identifiquei uma aba do Chrome. "
                    "Abra uma página e aguarde a extensão sincronizar."
                )
            comando["_aba_id"] = aba_id
            self._comandos.append(comando)

        inicio = time.time()

        while time.time() - inicio < timeout:
            with self._lock:
                resultado = self._resultados.pop(
                    identificador,
                    None
                )

            if resultado is not None:
                if not resultado.get("ok"):
                    raise ErroNavegadorJARVIS(
                        resultado.get(
                            "erro",
                            "A extensão não conseguiu executar a ação."
                        )
                    )

                return resultado.get(
                    "mensagem",
                    "Ação concluída."
                )

            time.sleep(0.15)

        # Remove o comando pendente para que ele não seja executado
        # inesperadamente caso a aba volte a responder mais tarde.
        with self._lock:
            self._comandos = [
                item for item in self._comandos
                if item.get("id") != identificador
            ]
            self._resultados.pop(identificador, None)

        raise ErroNavegadorJARVIS(
            "A extensão não respondeu a tempo. O comando pendente foi "
            "cancelado para evitar execução atrasada. Confirme se a aba "
            "continua ativa e tente novamente."
        )

    def estado_extensao(self):
        self._exigir_servidor()
        try:
            resposta = self._requisicao("/extension/status")
            estado = resposta.get("extensao") or {}
            atualizado = float(estado.get("ultima_atualizacao") or 0)
            estado["conectada"] = bool(
                atualizado and time.time() - atualizado < 8
            )
            estado["ativo"] = bool(estado.get("ativo") and estado["conectada"])
            return estado
        except Exception as erro:
            raise ErroNavegadorJARVIS(
                f"Não consegui consultar o estado da extensão: {erro}"
            ) from erro

    def estado(self):
        dados = self._obter_snapshot()

        return {
            "titulo": dados.get("titulo", ""),
            "url": dados.get("url", "")
        }

    def ler_pagina(self, limite_texto=14000):
        dados = self._obter_snapshot()

        dados["texto"] = str(
            dados.get("texto", "")
        )[:max(100, int(limite_texto))]

        return dados

    def abrir_url(self, url):
        url = (url or "").strip()

        if not url:
            raise ErroNavegadorJARVIS(
                "Informe um endereço."
            )

        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url

        partes = urlparse(url)

        if partes.scheme not in ("http", "https") or not partes.netloc:
            raise ErroNavegadorJARVIS(
                "Endereço inválido."
            )

        self._enviar_comando({
            "acao": "abrir_url",
            "url": url
        })

        return {
            "titulo": "",
            "url": url
        }

    def clicar_texto(self, texto, tipo="any", exato=False):
        if not (texto or "").strip():
            raise ErroNavegadorJARVIS(
                "Informe o texto do controle."
            )

        return self._enviar_comando({
            "acao": "clicar_texto",
            "texto": texto,
            "tipo": tipo,
            "exato": bool(exato)
        })

    def clicar(self, indice):
        return self._enviar_comando({
            "acao": "clicar_indice",
            "indice": int(indice)
        })

    def preencher_campo(self, identificador, valor):
        if not (identificador or "").strip():
            raise ErroNavegadorJARVIS(
                "Informe como identificar o campo."
            )

        return self._enviar_comando({
            "acao": "preencher",
            "identificador": identificador,
            "valor": str(valor)
        })

    def preencher(self, indice, valor):
        return self._enviar_comando({
            "acao": "preencher_indice",
            "indice": int(indice),
            "valor": str(valor)
        })

    def rolar(self, direcao="baixo", pixels=600):
        if direcao not in ("baixo", "cima"):
            raise ErroNavegadorJARVIS(
                "Direção inválida."
            )

        pixels = max(100, min(int(pixels), 1600))

        return self._enviar_comando({
            "acao": "rolar",
            "direcao": direcao,
            "pixels": pixels
        })

    def pressionar_tecla(self, tecla):
        permitidas = {
            "ENTER", "TAB", "ESC",
            "ARROWDOWN", "ARROWUP",
            "ARROWLEFT", "ARROWRIGHT",
            "HOME", "END", "PAGEUP", "PAGEDOWN"
        }

        tecla = (tecla or "").strip().upper()

        if tecla not in permitidas:
            raise ErroNavegadorJARVIS(
                "Essa tecla não está liberada."
            )

        return self._enviar_comando({
            "acao": "tecla",
            "tecla": tecla
        })

    def executar_acao(self, acao):
        if not isinstance(acao, dict):
            raise ErroNavegadorJARVIS(
                "A ação precisa ser um objeto."
            )

        tipo = acao.get("acao")

        if tipo == "abrir_url":
            resultado = self.abrir_url(
                str(acao.get("url", ""))
            )
            return f"Solicitei a abertura de {resultado['url']}"

        if tipo == "clicar":
            if "indice" in acao:
                return self.clicar(acao["indice"])

            return self.clicar_texto(
                str(acao.get("texto", "")),
                str(acao.get("tipo", "any")),
                bool(acao.get("exato", False))
            )

        if tipo == "preencher":
            if "indice" in acao:
                return self.preencher(
                    acao["indice"],
                    str(acao.get("valor", ""))
                )

            return self.preencher_campo(
                str(acao.get("campo", "")),
                str(acao.get("valor", ""))
            )

        if tipo == "rolar":
            return self.rolar(
                str(acao.get("direcao", "baixo")),
                int(acao.get("pixels", 600))
            )

        if tipo == "tecla":
            return self.pressionar_tecla(
                str(acao.get("tecla", ""))
            )

        raise ErroNavegadorJARVIS(
            "Ação não permitida. "
            "O envio automático de formulários não está disponível."
        )


if __name__ == "__main__":
    navegador = NavegadorJARVIS()

    print("=" * 50)
    print("TESTE DO NÚCLEO DE NAVEGAÇÃO DO JARVIS")
    print("=" * 50)

    try:
        print("\nIniciando ponte Python...")
        print(navegador.iniciar())

        input(
            "\nAbra o Chrome, ative a extensão nesta aba "
            "e pressione ENTER aqui..."
        )

        dados = navegador.ler_pagina()

        print("\nPágina recebida!")
        print("Título:", dados.get("titulo"))
        print("URL:", dados.get("url"))

        print("\nTexto da página:")
        print(dados.get("texto", "")[:8000])

        print("\nElementos encontrados:")

        for elemento in dados.get("elementos", []):
            print(
                f"{elemento.get('indice')}. "
                f"{elemento.get('tag')} | "
                f"{elemento.get('nome')}"
            )

    except ErroNavegadorJARVIS as erro:
        print("\nERRO:", erro)

    except Exception as erro:
        print(
            "\nERRO INESPERADO:",
            type(erro).__name__,
            erro
        )

    finally:
        navegador.parar()
        print("\nPonte encerrada.")
