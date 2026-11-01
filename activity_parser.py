"""Identifica e organiza questões de atividades a partir do texto visível de uma página.

Este módulo apenas extrai estrutura. Não responde, clica, preenche nem envia formulários.
"""
import re


def extrair_estrutura_atividade(snapshot):
    if isinstance(snapshot, str):
        texto, titulo, url = snapshot, "", ""
    elif isinstance(snapshot, dict):
        texto = str(snapshot.get("texto", "") or "")
        titulo = str(snapshot.get("titulo", "") or "")
        url = str(snapshot.get("url", "") or "")
    else:
        raise TypeError("A captura deve ser texto ou um dicionário.")

    linhas = [re.sub(r"\s+", " ", x).strip() for x in texto.splitlines()]
    linhas = [x for x in linhas if x]
    questoes = []
    atual = None
    alternativa = None

    padrao_q = re.compile(
        r"^(?:(?:quest[aã]o|quest[aã]o\s+de)\s*)?(\d{1,2})\s*[.)ºª:-]\s*(.*)$",
        re.I
    )
    padrao_questao = re.compile(r"^(quest[aã]o)\s*(\d{1,2})\s*[:.)-]?\s*(.*)$", re.I)
    padrao_alt = re.compile(r"^\(?([A-E])\)?\s*[).:-]\s*(.+)$", re.I)

    for linha in linhas:
        mq = padrao_questao.match(linha)
        if mq:
            atual = {"numero": int(mq.group(2)), "enunciado": mq.group(3).strip(), "alternativas": []}
            questoes.append(atual)
            alternativa = None
            continue

        mq = padrao_q.match(linha)
        if mq and (atual is None or int(mq.group(1)) != atual["numero"]):
            atual = {"numero": int(mq.group(1)), "enunciado": mq.group(2).strip(), "alternativas": []}
            questoes.append(atual)
            alternativa = None
            continue

        ma = padrao_alt.match(linha)
        if ma and atual is not None:
            alternativa = {"letra": ma.group(1).upper(), "texto": ma.group(2).strip()}
            atual["alternativas"].append(alternativa)
            continue

        if atual is not None:
            if alternativa is not None:
                alternativa["texto"] = (alternativa["texto"] + " " + linha).strip()
            else:
                atual["enunciado"] = (atual["enunciado"] + " " + linha).strip()

    for q in questoes:
        q["tipo"] = "múltipla escolha" if q["alternativas"] else "discursiva ou não identificada"

    return {
        "titulo": titulo,
        "url": url,
        "quantidade": len(questoes),
        "questoes": questoes,
        "confianca": "alta" if questoes and any(q["alternativas"] for q in questoes) else ("parcial" if questoes else "baixa"),
        "aviso": "" if questoes else "Não encontrei marcadores claros de questões. O texto pode precisar de revisão manual."
    }


def formatar_estrutura_para_ia(estrutura):
    partes = []
    if estrutura.get("titulo"):
        partes.append("Página: " + estrutura["titulo"])
    partes.append("Questões identificadas: " + str(estrutura["quantidade"]))
    for q in estrutura["questoes"]:
        partes.append(f'\nQuestão {q["numero"]} ({q["tipo"]}):')
        partes.append(q["enunciado"] or "[enunciado não identificado]")
        for alt in q["alternativas"]:
            partes.append(f'  {alt["letra"]}) {alt["texto"]}')
    if estrutura.get("aviso"):
        partes.append("\nAviso: " + estrutura["aviso"])
    return "\n".join(partes)
