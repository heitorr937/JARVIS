"use strict";

const BASE = "http://127.0.0.1:8765";
const CHAVE_ATIVO = "jarvis_global_ativo";

async function requisicao(caminho, dados = null) {
    const opcoes = dados === null
        ? { method: "GET" }
        : {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        };

    const resposta = await fetch(BASE + caminho, opcoes);
    if (!resposta.ok) throw new Error("Erro HTTP " + resposta.status);
    return await resposta.json();
}

function paginaCompatível(url) {
    return typeof url === "string" &&
        (url.startsWith("http://") || url.startsWith("https://"));
}

async function injetarNaAba(tabId, url) {
    if (!paginaCompatível(url)) return;
    const estado = await chrome.storage.local.get(CHAVE_ATIVO);
    if (estado[CHAVE_ATIVO] !== true) return;

    try {
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ["content.js"]
        });
    } catch (erro) {
        // Algumas páginas especiais ou protegidas não aceitam scripts.
        console.debug("JARVIS: não foi possível ativar nesta página:", erro.message);
    }
}

async function ativarGlobalmente() {
    await chrome.storage.local.set({ [CHAVE_ATIVO]: true });
    const abas = await chrome.tabs.query({});
    await Promise.all(abas.map(aba => injetarNaAba(aba.id, aba.url)));
    return abas.length;
}

async function desativarGlobalmente() {
    await chrome.storage.local.set({ [CHAVE_ATIVO]: false });
    const abas = await chrome.tabs.query({});
    await Promise.all(abas.map(async aba => {
        if (!aba.id) return;
        try {
            await chrome.tabs.sendMessage(aba.id, { tipo: "JARVIS_PARAR" });
        } catch (_) {
            // A aba pode não ter o content script carregado.
        }
    }));
    return abas.length;
}

chrome.tabs.onUpdated.addListener((tabId, info, aba) => {
    if (info.status === "complete") {
        injetarNaAba(tabId, aba.url);
    }
});

chrome.tabs.onCreated.addListener(aba => {
    if (aba.id && aba.url) injetarNaAba(aba.id, aba.url);
});

chrome.runtime.onMessage.addListener((mensagem, remetente, responder) => {
    (async () => {
        try {
            let resultado;

            switch (mensagem.tipo) {
                case "JARVIS_ATIVAR_GLOBAL":
                    resultado = { abas: await ativarGlobalmente(), ativo: true };
                    break;
                case "JARVIS_DESATIVAR_GLOBAL":
                    resultado = { abas: await desativarGlobalmente(), ativo: false };
                    break;
                case "JARVIS_STATUS_GLOBAL": {
                    const estado = await chrome.storage.local.get(CHAVE_ATIVO);
                    resultado = { ativo: estado[CHAVE_ATIVO] === true };
                    break;
                }
                case "JARVIS_SNAPSHOT":
                    resultado = await requisicao("/snapshot", mensagem.dados);
                    break;
                case "JARVIS_PROXIMO":
                    resultado = await requisicao("/next");
                    break;
                case "JARVIS_RESULTADO":
                    resultado = await requisicao("/resultado", mensagem.dados);
                    break;
                default:
                    responder({ ok: false, erro: "Mensagem desconhecida." });
                    return;
            }

            responder({ ok: true, resultado });
        } catch (erro) {
            console.error("Erro na ponte JARVIS:", erro);
            responder({ ok: false, erro: erro.message || String(erro) });
        }
    })();

    return true;
});

console.log("Ponte global de comunicação do JARVIS carregada.");