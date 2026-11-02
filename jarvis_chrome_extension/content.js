
(function () {
    "use strict";

    if (window.__JARVIS_EXTENSION_ATIVA__) {
        console.log("JARVIS já está ativo nesta aba.");
        return;
    }

    window.__JARVIS_EXTENSION_ATIVA__ = true;

    const INTERVALO = 500;
    const INTERVALO_LEITURA = 1500;

    let ativo = true;
    let executando = false;
    let ultimaLeitura = 0;

    const esperar = ms =>
        new Promise(resolve => setTimeout(resolve, ms));

    function elementosVisiveis() {
        const seletores = [
            "a", "button", "input", "textarea", "select",
            '[role="button"]', '[role="link"]'
        ];

        return [...document.querySelectorAll(seletores.join(","))]
            .filter(e => {
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);

                return r.width > 0 &&
                    r.height > 0 &&
                    s.display !== "none" &&
                    s.visibility !== "hidden";
            });
    }

    function nomeElemento(e) {
        return (
            e.innerText ||
            e.getAttribute("aria-label") ||
            e.getAttribute("placeholder") ||
            e.getAttribute("name") ||
            e.title ||
            ""
        ).trim().slice(0, 200);
    }

    function capturarPagina() {
        const elementos = elementosVisiveis()
            .slice(0, 200)
            .map((e, indice) => {
                if (!e.dataset.jv) {
                    e.dataset.jv =
                        "jv-" + Math.random().toString(36).slice(2, 10);
                }

                return {
                    indice,
                    id: e.dataset.jv,
                    tag: e.tagName.toLowerCase(),
                    nome: nomeElemento(e),
                    tipo: e.type || "",
                    href: e.href || "",
                    // Nunca transmitir valores digitados ou selecionados:
                    // podem conter senhas, dados pessoais ou informações financeiras.
                    valor: "",
                    seletor: "jv:" + e.dataset.jv
                };
            });

        return {
            url: location.href,
            titulo: document.title,
            texto: (document.body?.innerText || "").slice(0, 16000),
            elementos
        };
    }

    function localizarPorIndice(indice) {
        return elementosVisiveis()[Number(indice)] || null;
    }

    function localizarPorIdentificador(identificador) {
        const termo = String(identificador || "").trim();

        if (!termo) return null;

        if (termo.startsWith("jv:")) {
            const id = termo.slice(3);

            return [...document.querySelectorAll("[data-jv]")]
                .find(e => e.dataset.jv === id) || null;
        }

        const campos = [
            ...document.querySelectorAll(
                "input, textarea, [contenteditable='true']"
            )
        ];

        return campos.find(e => {
            const valores = [
                e.id,
                e.name,
                e.placeholder,
                e.getAttribute("aria-label")
            ];

            return valores.some(v =>
                v && v.toLowerCase().includes(termo.toLowerCase())
            );
        }) || null;
    }

    function validarCliqueSeguro(elemento) {
        if (!elemento) {
            throw new Error("Controle não encontrado.");
        }

        const tipo = String(elemento.type || "").toLowerCase();
        const nome = nomeElemento(elemento).toLowerCase();
        const rotulo = [
            nome,
            elemento.getAttribute("aria-label") || "",
            elemento.getAttribute("title") || "",
            elemento.getAttribute("name") || ""
        ].join(" ").toLowerCase();

        const acaoProibida =
            /\b(enviar|envie|mandar|manda|send|submit|entregar|finalizar|concluir|submeter|comprar|pagar|excluir|apagar|deletar|confirmar)\b/i;

        if (tipo === "submit" || elemento.tagName === "INPUT" &&
            ["submit", "image", "reset"].includes(tipo)) {
            throw new Error("Bloqueei um controle de envio ou submissão.");
        }

        if (acaoProibida.test(rotulo)) {
            throw new Error("Bloqueei um clique que pode enviar, confirmar ou finalizar uma ação.");
        }

        if (elemento.disabled || elemento.getAttribute("aria-disabled") === "true") {
            throw new Error("Este controle está desativado.");
        }
    }

    function clicarTexto(texto, tipo = "any", exato = false) {
        const termo = String(texto || "").trim().toLowerCase();

        if (!termo) {
            throw new Error("Texto do clique não informado.");
        }

        const encontrado = elementosVisiveis().find(e => {
            const nome = nomeElemento(e).toLowerCase();

            if (!nome) return false;

            const corresponde = exato
                ? nome === termo
                : nome.includes(termo);

            if (!corresponde) return false;

            if (tipo === "button") {
                return e.tagName === "BUTTON" ||
                    e.getAttribute("role") === "button";
            }

            if (tipo === "link") {
                return e.tagName === "A" ||
                    e.getAttribute("role") === "link";
            }

            return true;
        });

        if (!encontrado) {
            throw new Error("Não encontrei o controle: " + texto);
        }

        validarCliqueSeguro(encontrado);
        encontrado.scrollIntoView({ block: "center" });
        encontrado.click();

        return "Clique executado em: " + nomeElemento(encontrado);
    }

    function preencherElemento(elemento, valor) {
        if (!elemento) {
            throw new Error("Campo não encontrado.");
        }

        if (
            !["INPUT", "TEXTAREA"].includes(elemento.tagName) &&
            !elemento.isContentEditable
        ) {
            throw new Error("O elemento não é um campo de texto.");
        }

        if (
            elemento.disabled ||
            elemento.readOnly ||
            elemento.getAttribute("aria-disabled") === "true" ||
            elemento.getAttribute("aria-readonly") === "true"
        ) {
            throw new Error("Este campo está bloqueado para edição.");
        }

        if (
            elemento.tagName === "INPUT" &&
            !["text", "search", "email", "url", "tel", ""].includes(
                String(elemento.type || "").toLowerCase()
            )
        ) {
            throw new Error("Este tipo de campo não pode ser preenchido automaticamente. Senhas e códigos de autenticação nunca são preenchidos pelo JARVIS.");
        }

        if (String(valor ?? "").length > 5000) {
            throw new Error("O texto ultrapassa o limite permitido.");
        }

        elemento.scrollIntoView({ block: "center" });
        elemento.focus();

        const texto = String(valor ?? "");

        if (elemento.isContentEditable) {
            elemento.textContent = texto;
        } else {
            const prototipo = elemento.tagName === "TEXTAREA"
                ? HTMLTextAreaElement.prototype
                : HTMLInputElement.prototype;

            const setter = Object.getOwnPropertyDescriptor(
                prototipo,
                "value"
            )?.set;

            if (setter) {
                setter.call(elemento, texto);
            } else {
                elemento.value = texto;
            }
        }

        elemento.dispatchEvent(new Event("input", { bubbles: true }));
        elemento.dispatchEvent(new Event("change", { bubbles: true }));

        return "Campo preenchido. Nenhum formulário foi enviado.";
    }

    async function executarAcao(comando) {
        switch (comando.acao) {
            case "ler_pagina":
                return {
                    mensagem: "Leitura atualizada.",
                    dados: capturarPagina()
                };

            case "abrir_url": {
                const url = String(comando.url || "").trim();

                if (!/^https?:\/\//i.test(url)) {
                    throw new Error("Endereço inválido.");
                }

                location.assign(url);

                return {
                    mensagem: "Solicitei a abertura do endereço."
                };
            }

            case "clicar_texto":
                return {
                    mensagem: clicarTexto(
                        comando.texto,
                        comando.tipo,
                        comando.exato
                    )
                };

            case "clicar_indice": {
                const elemento = localizarPorIndice(comando.indice);

                if (!elemento) {
                    throw new Error("Controle não encontrado.");
                }

                validarCliqueSeguro(elemento);
                elemento.scrollIntoView({ block: "center" });
                elemento.click();

                return {
                    mensagem: "Clique executado em " + nomeElemento(elemento)
                };
            }

            case "preencher": {
                const elemento = localizarPorIdentificador(
                    comando.identificador
                );

                return {
                    mensagem: preencherElemento(elemento, comando.valor)
                };
            }

            case "preencher_indice": {
                const elemento = localizarPorIndice(comando.indice);

                return {
                    mensagem: preencherElemento(elemento, comando.valor)
                };
            }

            case "rolar": {
                const pixels = Math.max(
                    100,
                    Math.min(Number(comando.pixels) || 600, 1600)
                );

                window.scrollBy({
                    top: pixels * (comando.direcao === "cima" ? -1 : 1),
                    behavior: "smooth"
                });

                return { mensagem: "Página rolada." };
            }

            case "tecla": {
                const mapa = {
                    ENTER: "Enter",
                    TAB: "Tab",
                    ESC: "Escape",
                    ARROWDOWN: "ArrowDown",
                    ARROWUP: "ArrowUp",
                    ARROWLEFT: "ArrowLeft",
                    ARROWRIGHT: "ArrowRight",
                    HOME: "Home",
                    END: "End",
                    PAGEUP: "PageUp",
                    PAGEDOWN: "PageDown"
                };

                const tecla = String(comando.tecla || "").toUpperCase();

                if (!mapa[tecla] || tecla === "ENTER") {
                    throw new Error("Esta tecla está bloqueada para evitar envios acidentais.");
                }

                const elemento = document.activeElement || document.body;

                elemento.dispatchEvent(new KeyboardEvent("keydown", {
                    key: mapa[tecla],
                    bubbles: true
                }));

                elemento.dispatchEvent(new KeyboardEvent("keyup", {
                    key: mapa[tecla],
                    bubbles: true
                }));

                return { mensagem: "Tecla enviada: " + tecla };
            }

            default:
                throw new Error("Ação desconhecida: " + comando.acao);
        }
    }

    async function enviar(tipo, dados = null) {
        return chrome.runtime.sendMessage({ tipo, dados });
    }

    async function atualizarLeitura() {
        const resposta = await enviar(
            "JARVIS_SNAPSHOT",
            capturarPagina()
        );

        if (!resposta?.ok) {
            throw new Error(resposta?.erro || "Falha ao enviar leitura.");
        }

        ultimaLeitura = Date.now();
    }

    async function consultarComando() {
        const resposta = await enviar("JARVIS_PROXIMO");

        if (!resposta?.ok) {
            throw new Error(resposta?.erro || "Falha ao consultar comandos.");
        }

        return resposta.resultado?.comando || null;
    }

    async function enviarResultado(resultado) {
        const resposta = await enviar("JARVIS_RESULTADO", resultado);

        if (!resposta?.ok) {
            throw new Error(resposta?.erro || "Falha ao enviar resultado.");
        }
    }

    async function ciclo() {
        if (executando || !ativo) return;

        executando = true;

        try {
            while (ativo) {
                // Todas as abas podem ter o content script, mas somente a aba
                // visível deve alimentar a ponte compartilhada e consumir comandos.
                // Isso evita que uma aba em segundo plano "roube" a ação destinada
                // à página que o usuário está realmente utilizando.
                if (document.visibilityState !== "visible") {
                    await esperar(INTERVALO);
                    continue;
                }

                try {
                    if (Date.now() - ultimaLeitura >= INTERVALO_LEITURA) {
                        await atualizarLeitura();
                    }

                    const comando = await consultarComando();

                    if (!comando) {
                        await esperar(INTERVALO);
                        continue;
                    }

                    let resultado;

                    try {
                        // O Python pode ter expirado o comando depois de
                        // entregá-lo ao content script, mas antes da execução.
                        // Revalidar aqui evita executar ações antigas.
                        const expiracao = Number(comando._expira_em || 0);
                        if (!Number.isFinite(expiracao) || expiracao <= Date.now() / 1000) {
                            throw new Error("Comando expirado; não executei a ação.");
                        }

                        const retorno = await executarAcao(comando);

                        resultado = {
                            id: comando.id,
                            ok: true,
                            mensagem: retorno?.mensagem || "Ação concluída."
                        };
                    } catch (erro) {
                        resultado = {
                            id: comando.id,
                            ok: false,
                            erro: erro.message || String(erro)
                        };
                    }

                    await enviarResultado(resultado);
                    await esperar(200);

                } catch (erro) {
                    console.error("Erro de comunicação JARVIS:", erro);
                    await esperar(1000);
                }
            }
        } finally {
            executando = false;
        }
    }

    chrome.runtime.onMessage.addListener(
        (mensagem, remetente, responder) => {
            if (mensagem.tipo === "JARVIS_PARAR") {
                ativo = false;
                window.__JARVIS_EXTENSION_ATIVA__ = false;

                responder({ ok: true });
                return true;
            }
        }
    );

    console.log("JARVIS ativado nesta aba.");

    ciclo();
})();
