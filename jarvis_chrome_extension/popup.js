"use strict";

const status = document.getElementById("status");
const botaoAtivar = document.getElementById("ativar");
const botaoDesativar = document.getElementById("desativar");

async function enviar(tipo) {
    const resposta = await chrome.runtime.sendMessage({ tipo });
    if (!resposta?.ok) throw new Error(resposta?.erro || "Falha ao comunicar com o JARVIS.");
    return resposta.resultado;
}

function mostrarEstado(ativo, quantidade = null) {
    botaoAtivar.disabled = ativo;
    botaoDesativar.disabled = !ativo;
    status.textContent = ativo
        ? "JARVIS ATIVO em todas as abas" + (quantidade === null ? "" : " (" + quantidade + " abas verificadas)")
        : "JARVIS DESATIVADO globalmente";
}

async function atualizarEstado() {
    try {
        const resultado = await enviar("JARVIS_STATUS_GLOBAL");
        mostrarEstado(resultado.ativo);
    } catch (erro) {
        status.textContent = "Erro: " + erro.message;
    }
}

botaoAtivar.addEventListener("click", async () => {
    botaoAtivar.disabled = true;
    status.textContent = "Ativando em todas as abas...";
    try {
        const resultado = await enviar("JARVIS_ATIVAR_GLOBAL");
        mostrarEstado(true, resultado.abas);
    } catch (erro) {
        status.textContent = "Erro ao ativar: " + erro.message;
        await atualizarEstado();
    }
});

botaoDesativar.addEventListener("click", async () => {
    botaoDesativar.disabled = true;
    status.textContent = "Desativando em todas as abas...";
    try {
        const resultado = await enviar("JARVIS_DESATIVAR_GLOBAL");
        mostrarEstado(false, resultado.abas);
    } catch (erro) {
        status.textContent = "Erro ao desativar: " + erro.message;
        await atualizarEstado();
    }
});

atualizarEstado();