"""Políticas fail-closed para ações de entrega e submissão do JARVIS."""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping


_ACAO_DE_ENTREGA = re.compile(
    r"\b(entregar|entrega|enviar|envie|envia|mandar|manda|"
    r"finalizar|finalize|finaliza|concluir|conclua|submeter|submeta|"
    r"submit|send|finish|complete|confirmar|confirme|comprar|pagar|"
    r"excluir|apagar|deletar)\b",
    re.IGNORECASE,
)

# O rótulo precisa vir do controle real capturado no DOM. A descrição da
# ação é texto produzido pelo modelo e, sozinha, não prova qual elemento
# será manipulado.
_ALTERNATIVA = re.compile(
    r"\b(alternativa|opção|opcao|option|choice)\b",
    re.IGNORECASE,
)
_LETRA_ALTERNATIVA = re.compile(r"^[A-E](?:[).:\s]|$)", re.IGNORECASE)
_CAMPO_RESPOSTA = re.compile(
    r"\b(resposta|answer|campo|caixa|editor|textarea|text input|"
    r"campo de texto|área de resposta|area de resposta|"
    r"área de texto|area de texto)\b",
    re.IGNORECASE,
)


def acao_pode_submeter(acao: Mapping[str, Any]) -> bool:
    """Retorna True para ações que podem enviar, finalizar ou submeter dados."""
    if not isinstance(acao, Mapping):
        return False

    tipo = str(acao.get("type", "")).strip().lower()
    tecla = str(acao.get("key", "")).strip().lower()

    # Enter pode enviar formulários mesmo quando o botão não foi identificado.
    if tipo == "press" and tecla in {"enter", "return"}:
        return True

    if tipo != "click":
        return False

    descricao = str(acao.get("description", ""))
    rotulo = str(acao.get("target_label", ""))
    return bool(_ACAO_DE_ENTREGA.search(descricao + " " + rotulo))


def validar_acoes_por_tipo_questao(
    acoes: Iterable[Mapping[str, Any]],
    tipo_questao: str | None,
) -> None:
    """Permite somente interações coerentes com o tipo de questão identificado."""
    for acao in acoes or ():
        if not isinstance(acao, Mapping):
            raise ValueError("A ação da atividade é inválida.")

        tipo_acao = str(acao.get("type", "")).strip().lower()
        rotulo = str(acao.get("target_label", "")).strip()

        if tipo_acao == "scroll":
            continue

        # Durante atividades, teclas podem selecionar opções, avançar etapas
        # ou acionar formulários. A navegação deve usar controles DOM validados.
        if tipo_acao == "press":
            raise ValueError("Ações de teclado estão bloqueadas durante atividades.")

        if tipo_acao == "type":
            if tipo_questao != "written":
                raise ValueError(
                    "Só posso preencher texto quando a questão for identificada como discursiva."
                )
            if not _CAMPO_RESPOSTA.search(rotulo):
                raise ValueError(
                    "Só posso digitar em um controle identificado como campo de resposta."
                )
            continue

        if tipo_acao == "click":
            if tipo_questao == "multiple_choice":
                if not (
                    _ALTERNATIVA.search(rotulo)
                    or _LETRA_ALTERNATIVA.match(rotulo)
                ):
                    raise ValueError(
                        "Em múltipla escolha, só posso clicar em uma alternativa identificada."
                    )
                continue

            if tipo_questao == "written":
                if not _CAMPO_RESPOSTA.search(rotulo):
                    raise ValueError(
                        "Em questão discursiva, só posso clicar no campo de resposta identificado."
                    )
                continue

            raise ValueError(
                "Não vou clicar em controles de atividade sem identificar o tipo da questão."
            )

        raise ValueError("A ação não é permitida durante a resolução de atividades.")


def bloquear_entrega_atividade(acoes: Iterable[Mapping[str, Any]]) -> None:
    """Interrompe planos com qualquer ação de submissão.

    A entrega automática permanece desativada até existir um fluxo separado
    que apresente a resposta final e peça confirmação imediatamente antes
    de submeter. Um pedido genérico ou instrução do modelo não é confirmação.
    """
    for acao in acoes or ():
        if acao_pode_submeter(acao):
            raise ValueError(
                "Bloqueei a entrega automática da atividade. "
                "O JARVIS pode preencher ou marcar respostas, mas não pode "
                "enviar, finalizar ou submeter a atividade nesta versão."
            )
