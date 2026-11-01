
"use strict";

const status = document.getElementById("status");

document.getElementById("ativar").addEventListener("click", async () => {
    try {
        const [aba] = await chrome.tabs.query({
            active: true,
            currentWindow: true
        });

        if (!aba || !aba.id) {
            throw new Error("Não encontrei a aba atual.");
        }

        await chrome.scripting.executeScript({
            target: { tabId: aba.id },
            files: ["content.js"]
        });

        status.textContent =
            "JARVIS ativado nesta aba!";

    } catch (erro) {
        status.textContent = "Erro: " + erro.message;
    }
});

document.getElementById("desativar").addEventListener("click", async () => {
    try {
        const [aba] = await chrome.tabs.query({
            active: true,
            currentWindow: true
        });

        if (!aba || !aba.id) {
            throw new Error("Não encontrei a aba atual.");
        }

        await chrome.tabs.sendMessage(aba.id, {
            tipo: "JARVIS_PARAR"
        });

        status.textContent = "JARVIS desativado nesta aba.";

    } catch (erro) {
        status.textContent =
            "A extensão não estava ativa nesta aba.";
    }
});
