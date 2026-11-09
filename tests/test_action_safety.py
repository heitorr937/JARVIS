import unittest

from action_safety import (
    acao_pode_submeter,
    bloquear_entrega_atividade,
    validar_acoes_por_tipo_questao,
)


class TestActionSafety(unittest.TestCase):
    def test_bloqueia_botao_entregar(self):
        acao = {
            "type": "click",
            "description": "Clique no botão de entrega",
            "target_label": "Entregar atividade",
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
            "Concluir tarefa",
        ):
            with self.subTest(rotulo=rotulo):
                self.assertTrue(
                    acao_pode_submeter(
                        {
                            "type": "click",
                            "description": "Clicar",
                            "target_label": rotulo,
                        }
                    )
                )

    def test_bloqueia_enter(self):
        acao = {"type": "press", "key": "enter", "description": "Pressionar Enter"}
        self.assertTrue(acao_pode_submeter(acao))
        with self.assertRaises(ValueError):
            bloquear_entrega_atividade([acao])

    def test_permite_alternativa_e_preenchimento_identificados(self):
        alternativa = {
            "type": "click",
            "description": "Selecionar alternativa",
            "target_label": "A) Regular a temperatura",
        }
        clique_resposta = {
            "type": "click",
            "description": "Clicar no campo de resposta",
            "target_label": "Resposta",
        }
        digitar = {
            "type": "type",
            "description": "Preencher resposta",
            "text": "Explicação",
        }
        validar_acoes_por_tipo_questao([alternativa], "multiple_choice")
        validar_acoes_por_tipo_questao([clique_resposta, digitar], "written")
        bloquear_entrega_atividade([alternativa, clique_resposta, digitar])

    def test_permite_navegacao_sem_submissao(self):
        bloquear_entrega_atividade(
            [{"type": "click", "description": "Abrir próxima questão", "target_label": "Próxima questão"}]
        )

    def test_multipla_escolha_so_permite_alternativa_real(self):
        validar_acoes_por_tipo_questao(
            [{"type": "click", "description": "Selecionar", "target_label": "A) Resposta correta"}],
            "multiple_choice",
        )
        with self.assertRaisesRegex(ValueError, "só posso clicar em uma alternativa"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Selecionar alternativa", "target_label": "Continuar"}],
                "multiple_choice",
            )

    def test_descricao_do_modelo_nao_autoriza_campo(self):
        with self.assertRaisesRegex(ValueError, "campo de resposta identificado"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Campo de resposta", "target_label": "Enviar atividade"}],
                "written",
            )

    def test_discursiva_exige_campo_identificado_antes_de_digitar(self):
        with self.assertRaisesRegex(ValueError, "identificar um campo de resposta"):
            validar_acoes_por_tipo_questao(
                [{"type": "type", "description": "Preencher resposta", "text": "Texto"}],
                "written",
            )
        validar_acoes_por_tipo_questao(
            [
                {"type": "click", "target_label": "Resposta"},
                {"type": "type", "text": "Texto"},
            ],
            "written",
        )
        # No controle iterativo, o clique de foco ocorreu no passo anterior.
        validar_acoes_por_tipo_questao(
            [{"type": "type", "text": "Texto"}],
            "written",
            campo_resposta_previamente_focado=True,
        )

    def test_discursiva_exige_campo_identificado_para_clicar(self):
        validar_acoes_por_tipo_questao(
            [{"type": "click", "description": "Campo", "target_label": "Resposta"}],
            "written",
        )
        with self.assertRaisesRegex(ValueError, "campo de resposta identificado"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "description": "Campo de resposta", "target_label": "Continuar"}],
                "written",
            )

    def test_rotulo_generico_campo_nao_autoriza_digitar(self):
        with self.assertRaisesRegex(ValueError, "identificar um campo de resposta"):
            validar_acoes_por_tipo_questao(
                [
                    {"type": "click", "target_label": "Campo"},
                    {"type": "type", "text": "Texto"},
                ],
                "written",
            )

    def test_bloqueia_teclas_durante_atividade(self):
        for tecla in ("enter", "tab", "space", "arrowdown"):
            with self.subTest(tecla=tecla):
                with self.assertRaisesRegex(ValueError, "teclado estão bloqueadas"):
                    validar_acoes_por_tipo_questao(
                        [{"type": "press", "key": tecla}],
                        "multiple_choice",
                    )

    def test_tipo_desconhecido_nao_permite_cliques(self):
        validar_acoes_por_tipo_questao([{"type": "scroll"}], "unknown")
        with self.assertRaisesRegex(ValueError, "sem identificar o tipo"):
            validar_acoes_por_tipo_questao(
                [{"type": "click", "target_label": "Continuar"}],
                "unknown",
            )

    def test_tipo_de_acao_desconhecido_e_bloqueado(self):
        with self.assertRaisesRegex(ValueError, "não é permitida"):
            validar_acoes_por_tipo_questao(
                [{"type": "navigate", "target_label": "Resposta"}],
                "written",
            )

    def test_nao_confunde_texto_digitado_com_envio(self):
        acao = {
            "type": "type",
            "description": "Digitar a palavra enviar no campo",
            "target_label": "Resposta",
        }
        self.assertFalse(acao_pode_submeter(acao))


if __name__ == "__main__":
    unittest.main()
