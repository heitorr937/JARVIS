"""Políticas fail-closed para ações de entrega e submissão do JARVIS."""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Any


_ACAO_DE_ENTREGA = re.compile(
    r"\b(entregar|entrega|enviar|envie|envia|mandar|manda|"
    r"finalizar|finalize|finaliza|concluir|conclua|submeter|submeta|"
    r"submit|send|finish|complete|confirmar|confirme|comprar|pagar|"
    r"excluir|apagar|deletar)\b",
    re.IGNORECASE
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
