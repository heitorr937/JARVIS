import json
import os
import socket
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

from browser_navigator import ErroNavegadorJARVIS, NavegadorJARVIS


EXTENSION_ID = "jarvis-test-extension"


def porta_livre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestNavegadorHTTP(unittest.TestCase):
    def setUp(self):
        self.valor_anterior = os.environ.get("JARVIS_EXTENSION_ID")
        os.environ["JARVIS_EXTENSION_ID"] = EXTENSION_ID
        self.porta = porta_livre()
        self.navegador = NavegadorJARVIS(porta=self.porta)
        self.navegador.iniciar()
        self.base = self.navegador.endereco

    def tearDown(self):
        self.navegador.parar()
        if self.valor_anterior is None:
            os.environ.pop("JARVIS_EXTENSION_ID", None)
        else:
            os.environ["JARVIS_EXTENSION_ID"] = self.valor_anterior

    def requisitar(self, caminho, metodo="GET", dados=None, origem=None, host=None):
        corpo = None if dados is None else (
            dados if isinstance(dados, bytes)
            else json.dumps(dados).encode("utf-8")
        )
        cabecalhos = {}
        if corpo is not None:
            cabecalhos["Content-Type"] = "application/json"
        if origem is not None:
            cabecalhos["Origin"] = origem
        if host is not None:
            cabecalhos["Host"] = host

        pedido = urllib.request.Request(
            self.base + caminho,
            data=corpo,
            headers=cabecalhos,
            method=metodo
        )
        try:
            with urllib.request.urlopen(pedido, timeout=3) as resposta:
                return resposta.status, resposta.headers, resposta.read()
        except urllib.error.HTTPError as erro:
            return erro.code, erro.headers, erro.read()

    def test_health_sem_origin(self):
        status, _, corpo = self.requisitar("/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)["ok"])

    def test_rejeita_origin_de_site_comum(self):
        status, _, corpo = self.requisitar(
            "/health",
            origem="https://site-malicioso.example"
        )
        self.assertEqual(status, 403)
        self.assertFalse(json.loads(corpo)["ok"])

    def test_aceita_apenas_extensao_configurada(self):
        status, headers, corpo = self.requisitar(
            "/health",
            origem=f"chrome-extension://{EXTENSION_ID}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            headers.get("Access-Control-Allow-Origin"),
            f"chrome-extension://{EXTENSION_ID}"
        )
        self.assertTrue(json.loads(corpo)["ok"])

    def test_preflight_rejeita_origin_nao_autorizada(self):
        status, _, _ = self.requisitar(
            "/snapshot",
            metodo="OPTIONS",
            origem="https://site-malicioso.example"
        )
        self.assertEqual(status, 403)

    def test_preflight_autorizado(self):
        status, headers, _ = self.requisitar(
            "/snapshot",
            metodo="OPTIONS",
            origem=f"chrome-extension://{EXTENSION_ID}"
        )
        self.assertEqual(status, 204)
        self.assertEqual(
            headers.get("Access-Control-Allow-Origin"),
            f"chrome-extension://{EXTENSION_ID}"
        )
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_rejeita_host_nao_local(self):
        status, _, _ = self.requisitar(
            "/health",
            host="127.0.0.1:1"
        )
        self.assertEqual(status, 403)

    def test_json_invalido_retorna_400(self):
        status, _, _ = self.requisitar(
            "/snapshot",
            metodo="POST",
            dados=b"{json-invalido"
        )
        self.assertEqual(status, 400)

    def test_limite_de_corpo_retorna_413(self):
        corpo = b"x" * (2 * 1024 * 1024 + 1)
        status, _, _ = self.requisitar(
            "/snapshot",
            metodo="POST",
            dados=corpo
        )
        self.assertEqual(status, 413)

    def test_rota_desconhecida_retorna_404(self):
        status, _, _ = self.requisitar("/rota-inexistente")
        self.assertEqual(status, 404)

    def test_snapshot_e_status_da_extensao(self):
        status, _, _ = self.requisitar(
            "/snapshot",
            metodo="POST",
            dados={
                "titulo": "Página de teste",
                "url": "https://example.com/",
                "_jarvis_tab_id": 7
            }
        )
        self.assertEqual(status, 200)

        status, _, corpo = self.requisitar("/snapshot")
        self.assertEqual(status, 200)
        self.assertEqual(
            json.loads(corpo)["snapshot"]["_jarvis_tab_id"],
            7
        )

        status, _, _ = self.requisitar(
            "/extension/status",
            metodo="POST",
            dados={"ativo": True, "titulo": "Teste", "url": "https://example.com/"}
        )
        self.assertEqual(status, 200)

        status, _, corpo = self.requisitar("/extension/status")
        estado = json.loads(corpo)["extensao"]
        self.assertEqual(status, 200)
        self.assertTrue(estado["ativo"])
        self.assertEqual(estado["aba"]["titulo"], "Teste")

    def test_comando_e_resultado_correlacionados(self):
        with self.navegador._lock:
            self.navegador._snapshot = {"_jarvis_tab_id": 42}

        resultado = {}

        def enviar():
            try:
                resultado["valor"] = self.navegador._enviar_comando(
                    {"acao": "teste"}, timeout=3
                )
            except Exception as erro:
                resultado["erro"] = erro

        thread = threading.Thread(target=enviar)
        thread.start()

        comando = None
        prazo = time.monotonic() + 2
        while time.monotonic() < prazo and comando is None:
            status, _, corpo = self.requisitar("/next?tab_id=42")
            self.assertEqual(status, 200)
            comando = json.loads(corpo).get("comando")
            if comando is None:
                time.sleep(0.03)

        self.assertIsNotNone(comando, "O comando não chegou à aba correta.")
        self.assertEqual(comando["_aba_id"], 42)

        status, _, _ = self.requisitar(
            "/resultado",
            metodo="POST",
            dados={
                "id": comando["id"],
                "ok": True,
                "mensagem": "Ação de teste concluída."
            }
        )
        self.assertEqual(status, 200)

        thread.join(timeout=2)
        self.assertFalse(thread.is_alive(), "A espera do resultado não terminou.")
        self.assertEqual(resultado.get("valor"), "Ação de teste concluída.")
        self.assertNotIn("erro", resultado)

    def test_timeout_remove_comando_pendente(self):
        with self.navegador._lock:
            self.navegador._snapshot = {"_jarvis_tab_id": 99}

        resultado = {}

        def enviar():
            try:
                self.navegador._enviar_comando(
                    {"acao": "nao_responder"}, timeout=0.5
                )
            except Exception as erro:
                resultado["erro"] = erro

        thread = threading.Thread(target=enviar)
        thread.start()

        comando = None
        prazo = time.monotonic() + 2
        while time.monotonic() < prazo and comando is None:
            status, _, corpo = self.requisitar("/next?tab_id=99")
            self.assertEqual(status, 200)
            comando = json.loads(corpo).get("comando")
            if comando is None:
                time.sleep(0.02)

        self.assertIsNotNone(comando, "O comando não foi entregue à extensão.")
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive(), "O timeout não encerrou a espera.")
        self.assertIsInstance(resultado.get("erro"), ErroNavegadorJARVIS)
        self.assertIn("cancelado", str(resultado["erro"]).lower())

        with self.navegador._lock:
            self.assertFalse(any(
                item.get("id") == comando["id"]
                for item in self.navegador._comandos
            ))


if __name__ == "__main__":
    unittest.main()
