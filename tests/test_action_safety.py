import unittest

from action_safety import (
    acao_pode_submeter,
    bloquear_entrega_atividade,
    validar_acoes_por_tipo_questao
)


class TestActionSafety(unittest.TestCase):
    def test_bloqueia_botao_entregar(self):
        acao = {
            "type": "click",
            "description": "Clique no botão de entrega",
            "target_label": "Entregar atividade"
        }
        self.assertTrue(acao_pode_submeter(acao))
        with self.assertRaisesRegex(ValueError, "Bloqueei a entrega automática"):
            bloquear_entrega_atividade([acao])

    def test_bloqueia_variacoes_de_submissao(self):
        for rotulo in (
            "Enviar respostas",
            "Finalizar atividade",
            "Submeter",
            "Submit",
            "Confirmar pagamento",
            "Concluir tarefa"
        ):
            with self.subTest(rotulo=rotulo):
                self.assertTrue(acao_pode_submeter({
                    "type": "click",
                    "description": "Clicar",
                    "target_label": rotulo
                }))

    def test_bloqueia_enter(self):
        self.assertTrue(acao_pode_submeter({
            "type": "press",
            "key": "enter",
            "description": "Pressionar Enter"
        }))
        with self.assertRaises(ValueError):
            bloquear_entrega_atividade([{
                "type": "press",
                "key": "enter"
            }])

    def test_permite_alternativa_e_preenchimento(self):
        acoes = [
            {
                "type": "click",
                "description": "Selecionar alternativa",
                "target_label": "A) Regular a temperatura"
            },
            {
                "type": "type",
                "description": "Preencher campo de resposta",
                "target_label": "Resposta"
            }
        ]
        self.assertFalse(any(acao_pode_submeter(a) for a in acoes))
        bloquear_entrega_atividade(acoes)

    def test_permite_navegacao_sem_submissao(self):
        acoes = [
            {
                "type": "click",
                "description": "Abrir próxima questão",
                "target_label": "Próxima questão"
            }
        ]
        bloquear_entrega_atividade(acoes)

    def test_multipla_escolha_so_permite_alternativa(self):
        validar_acoes_por_tipo_questao(
            [{"type": "click", "description": "Selecionar", "target_label": "A) Resposta correta"}],
            "multiple_choice"
        )
        with self.assertRaisesRegex(ValueError, "só posso clicar em uma alternativa"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Avançar", "target_label": "Continuar"}],
                "multiple_choice"
            )

    def test_discursiva_so_permite_campo_e_texto(self):
        validar_acoes_por_tipo_questao(
            [
                {"type": "click", "description": "Campo de resposta", "target_label": "Resposta"},
                {"type": "type", "description": "Preencher resposta", "text": "Explicação"}
            ],
            "written"
        )
        with self.assertRaisesRegex(ValueError, "campo de resposta identificado"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Avançar", "target_label": "Continuar"}],
                "written"
            )

    def test_tipo_desconhecido_nao_permite_cliques(self):
        validar_acoes_por_tipo_questao(
            [{"type": "scroll", "description": "Rolar"}],
            "unknown"
        )
        with self.assertRaisesRegex(ValueError, "sem identificar o tipo"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Avançar", "target_label": "Continuar"}],
                "unknown"
            )

    def test_nao_confunde_texto_de_digitar_com_envio(self):
        acao = {
            "type": "type",
            "description": "Digitar a palavra enviar no campo",
            "target_label": "Resposta"
        }
        self.assertFalse(acao_pode_submeter(acao))


if __name__ == "__main__":
    unittest.main()
