import unittest

from activity_parser import extrair_estrutura_atividade, formatar_estrutura_para_ia


class TestActivityParser(unittest.TestCase):
    def test_multipla_escolha(self):
        dados = {
            "titulo": "Atividade de Ciências",
            "url": "https://one.geekie.com.br/",
            "texto": (
                "Questão 1\nQual é a função da água?\n"
                "A) Regular a temperatura\nB) Produzir luz\n"
                "C) Formar rochas\nD) Criar oxigênio\n"
                "Questão 2\nExplique sua resposta."
            )
        }
        resultado = extrair_estrutura_atividade(dados)
        self.assertEqual(resultado["quantidade"], 2)
        self.assertEqual(len(resultado["questoes"][0]["alternativas"]), 4)
        self.assertEqual(resultado["questoes"][1]["tipo"], "discursiva ou não identificada")
        self.assertIn("Questões identificadas: 2", formatar_estrutura_para_ia(resultado))

    def test_numeracao_simples(self):
        texto = "1. Primeiro enunciado\nA) Opção A\nB) Opção B\n2) Segundo enunciado"
        resultado = extrair_estrutura_atividade(texto)
        self.assertEqual(resultado["quantidade"], 2)
        self.assertEqual(resultado["questoes"][0]["alternativas"][1]["letra"], "B")

    def test_nao_inventa_questoes(self):
        resultado = extrair_estrutura_atividade("Bem-vindo à plataforma. Nenhuma questão visível.")
        self.assertEqual(resultado["quantidade"], 0)
        self.assertTrue(resultado["aviso"])

    def test_entrada_invalida(self):
        with self.assertRaises(TypeError):
            extrair_estrutura_atividade(None)


if __name__ == "__main__":
    unittest.main()
