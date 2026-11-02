
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
            "a", "button", "input", "textarea", "select", "label",
            '[role="button"]', '[role="link"]', '[role="checkbox"]',
            '[role="radio"]', '[role="option"]', '[role="combobox"]',
            '[role="menuitem"]', '[role="tab"]'
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
        const rotuloAssociado = e.labels
            ? [...e.labels].map(label => label.innerText || label.textContent || "").join(" ")
            : "";
        const idsRotulo = String(e.getAttribute("aria-labelledby") || "")
            .split(/\s+/)
            .filter(Boolean);
        const rotuloReferenciado = idsRotulo
            .map(id => document.getElementById(id)?.innerText || "")
            .join(" ");

        return (
            e.innerText ||
            e.getAttribute("aria-label") ||
            rotuloReferenciado ||
            rotuloAssociado ||
            e.getAttribute("placeholder") ||
            e.getAttribute("name") ||
            e.title ||
            ""
        ).trim().slice(0, 200);
    }

    function localizarAreaRolagem() {
        const documento = document.scrollingElement || document.documentElement;
        const candidatos = [{ elemento: documento, prioridade: 1 }];

        for (const elemento of document.querySelectorAll("body *")) {
            if (elemento === documento || elemento === document.body) continue;
            const estilo = getComputedStyle(elemento);
            const rolagemVertical = ["auto", "scroll", "overlay"].includes(estilo.overflowY);
            if (!rolagemVertical || elemento.scrollHeight <= elemento.clientHeight + 80) continue;
            const retangulo = elemento.getBoundingClientRect();
            if (retangulo.width < 160 || retangulo.height < 120) continue;
            if (retangulo.bottom <= 0 || retangulo.top >= window.innerHeight) continue;
            if (estilo.display === "none" || estilo.visibility === "hidden") continue;

            // Evita escolher barras laterais e menus quando há uma região
            // principal ou artigo rolável na página.
            const semantico = elemento.matches(
                "main, article, [role='main'], [data-testid*='main' i]"
            ) || Boolean(elemento.closest("main, [role='main']"));
            candidatos.push({
                elemento,
                prioridade: semantico ? 2.5 : 1
            });
        }

        return candidatos.reduce((melhor, atual) => {
            const peso = ({ elemento, prioridade }) => {
                const largura = Math.max(0, elemento.clientWidth);
                const altura = Math.max(0, elemento.clientHeight);
                const area = largura * altura;
                const proporcaoConteudo =
                    elemento.scrollHeight / Math.max(1, altura);
                return prioridade * area * Math.log1p(proporcaoConteudo);
            };
            return peso(atual) > peso(melhor) ? atual : melhor;
        }).elemento;
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
                    role: e.getAttribute("role") || "",
                    nome: nomeElemento(e),
                    tipo: e.type || "",
                    desabilitado: Boolean(e.disabled || e.getAttribute("aria-disabled") === "true"),
                    obrigatorio: Boolean(e.required),
                    href: e.href || "",
                    // Nunca transmitir valores digitados ou selecionados:
                    // podem conter senhas, dados pessoais ou informações financeiras.
                    valor: "",
                    opcoes: e.tagName === "SELECT"
                        ? [...e.options].slice(0, 40).map((opcao, indice) => ({
                            indice,
                            texto: (opcao.textContent || "").trim().slice(0, 120),
                            valor: String(opcao.value || "").slice(0, 120),
                            desabilitada: Boolean(opcao.disabled)
                        }))
                        : [],
                    marcado: ["checkbox", "radio"].includes(String(e.type || "").toLowerCase())
                        ? Boolean(e.checked)
                        : null,
                    indice_selecionado: e.tagName === "SELECT" ? e.selectedIndex : null,
                    tem_valor: e.type === "password"
                        ? null
                        : (["INPUT", "TEXTAREA"].includes(e.tagName)
                            ? Boolean(e.value)
                            : (e.isContentEditable ? Boolean(e.textContent) : null)),
                    seletor: "jv:" + e.dataset.jv
                };
            });

        const textoVisivel = (() => {
            if (!document.body) return "";
            const linhas = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode(no) {
                        const pai = no.parentElement;
                        if (!pai || !no.nodeValue || !no.nodeValue.trim()) {
                            return NodeFilter.FILTER_REJECT;
                        }
                        if (pai.closest("script, style, noscript, template, [aria-hidden='true']")) {
                            return NodeFilter.FILTER_REJECT;
                        }
                        const estilo = getComputedStyle(pai);
                        if (estilo.display === "none" || estilo.visibility === "hidden") {
                            return NodeFilter.FILTER_REJECT;
                        }
                        const ret = document.createRange();
                        ret.selectNodeContents(no);
                        const visivel = [...ret.getClientRects()].some(r =>
                            r.bottom > 0 && r.top < window.innerHeight &&
                            r.right > 0 && r.left < window.innerWidth
                        );
                        return visivel ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                    }
                }
            );
            while (walker.nextNode()) {
                const trecho = walker.currentNode.nodeValue.replace(/\s+/g, " ").trim();
                if (trecho) linhas.push(trecho);
            }
            return linhas.join("\n").slice(0, 16000);
        })();

        return {
            url: location.href,
            titulo: document.title,
            texto: textoVisivel,
            rolagem: (() => {
                const area = localizarAreaRolagem();
                const topo = Math.round(area.scrollTop || 0);
                const altura = Math.max(area.scrollHeight || 0, area.clientHeight || 0);
                const viewport = area.clientHeight || window.innerHeight || 0;
                return {
                    topo,
                    altura,
                    viewport,
                    tipo: area === (document.scrollingElement || document.documentElement) ? "documento" : "painel",
                    chegou_ao_final: Math.ceil(topo + viewport) >= altura - 8
                };
            })(),
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

        const controleAssociado = elemento.tagName === "LABEL"
            ? (elemento.control || document.getElementById(elemento.htmlFor))
            : null;

        if (
            elemento.disabled ||
            elemento.getAttribute("aria-disabled") === "true" ||
            controleAssociado?.disabled
        ) {
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

    function selecionarOpcao(elemento, opcaoSolicitada) {
        if (!elemento || elemento.tagName !== "SELECT") {
            throw new Error("O controle indicado não é uma lista de seleção.");
        }
        if (elemento.disabled || elemento.getAttribute("aria-disabled") === "true") {
            throw new Error("Esta lista está desativada.");
        }

        const termo = String(opcaoSolicitada || "").trim();
        if (!termo || termo.length > 200) {
            throw new Error("A opção solicitada é inválida.");
        }

        const opcoes = [...elemento.options];
        const encontrada = opcoes.find(opcao =>
            !opcao.disabled &&
            (
                String(opcao.value) === termo ||
                (opcao.textContent || "").trim().toLowerCase() === termo.toLowerCase()
            )
        );

        if (!encontrada) {
            throw new Error("Não encontrei essa opção na lista.");
        }

        const setter = Object.getOwnPropertyDescriptor(
            HTMLSelectElement.prototype,
            "value"
        )?.set;
        if (setter) {
            setter.call(elemento, encontrada.value);
        } else {
            elemento.value = encontrada.value;
        }
        elemento.dispatchEvent(new Event("input", { bubbles: true }));
        elemento.dispatchEvent(new Event("change", { bubbles: true }));
        return "Opção selecionada: " + (encontrada.textContent || encontrada.value).trim();
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

        const tipoInput = String(elemento.type || "").toLowerCase();
        const tiposPermitidos = [
            "text", "search", "email", "url", "tel", "",
            "number", "date", "time", "month", "week"
        ];
        const metadadosCampo = [
            elemento.id,
            elemento.name,
            elemento.getAttribute("placeholder"),
            elemento.getAttribute("aria-label"),
            elemento.getAttribute("autocomplete")
        ].filter(Boolean).join(" ").toLowerCase();
        const pareceAutenticacao = /password|passwd|senha|one.?time.?code|otp|verification.?code|verificacao|autenticacao|auth.?code|security.?code|(^|\W)pin(\W|$)|c[oó]digo.{0,20}(autentic|verific|seguran|acesso)|(autentic|verific|seguran|acesso).{0,20}c[oó]digo/i.test(metadadosCampo);

        if (
            pareceAutenticacao ||
            (
                elemento.tagName === "INPUT" &&
                !tiposPermitidos.includes(tipoInput)
            )
        ) {
            throw new Error("Este campo parece conter senha ou código de autenticação e não será preenchido pelo JARVIS.");
        }

        const textoInformado = String(valor ?? "");
        if (tipoInput === "number" && textoInformado.trim() !== "" && !Number.isFinite(Number(textoInformado))) {
            throw new Error("O valor numérico informado é inválido.");
        }
        if (tipoInput === "date" && textoInformado && !/^\d{4}-\d{2}-\d{2}$/.test(textoInformado)) {
            throw new Error("A data precisa estar no formato AAAA-MM-DD.");
        }
        if (tipoInput === "time" && textoInformado && !/^\d{2}:\d{2}(?::\d{2})?$/.test(textoInformado)) {
            throw new Error("O horário precisa estar no formato HH:MM.");
        }
        if (tipoInput === "month" && textoInformado && !/^\d{4}-\d{2}$/.test(textoInformado)) {
            throw new Error("O mês precisa estar no formato AAAA-MM.");
        }
        if (tipoInput === "week" && textoInformado && !/^\d{4}-W\d{2}$/.test(textoInformado)) {
            throw new Error("A semana precisa estar no formato AAAA-Www.");
        }

        if (textoInformado.length > 5000) {
            throw new Error("O texto ultrapassa o limite permitido.");
        }

        elemento.scrollIntoView({ block: "center" });
        elemento.focus();

        const texto = textoInformado;

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

                return {
                    mensagem: "Solicitei a abertura do endereço.",
                    navegarDepois: url
                };

                return {
                    mensagem: "Solicitei a abertura do endereço."
                };
            }

            case "pesquisar": {
                const termo = String(comando.termo || "").trim();
                const host = location.hostname.toLowerCase();

                if (!termo || termo.length > 300) {
                    throw new Error("O termo de pesquisa é inválido.");
                }

                // A pesquisa automática só é permitida no Google.
                const buscadores = [
                    "google.com", "www.google.com", "google.com.br",
                    "www.google.com.br"
                ];
                if (!buscadores.includes(host)) {
                    throw new Error("Por segurança, a pesquisa automática está liberada apenas no Google.");
                }

                const destino = new URL("/search", location.origin);
                destino.searchParams.set("q", termo);

                return {
                    mensagem: "Pesquisa preparada no Google: " + termo,
                    navegarDepois: destino.href
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

            case "clicar_identificador": {
                const elemento = localizarPorIdentificador(
                    comando.identificador
                );

                if (!elemento || !elemento.isConnected) {
                    throw new Error(
                        "O controle mudou desde a leitura. Atualize a página antes de tentar novamente."
                    );
                }

                validarCliqueSeguro(elemento);
                elemento.scrollIntoView({ block: "center" });
                elemento.click();

                return {
                    mensagem: "Clique executado em " + nomeElemento(elemento)
                };
            }

            case "selecionar": {
                const elemento = localizarPorIdentificador(comando.identificador);
                return {
                    mensagem: selecionarOpcao(elemento, comando.opcao)
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

                const area = localizarAreaRolagem();
                area.scrollBy({
                    top: pixels * (comando.direcao === "cima" ? -1 : 1),
                    behavior: "smooth"
                });

                return { mensagem: "Área principal da página rolada." };
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
                    let retorno = null;

                    try {
                        // O Python pode ter expirado o comando depois de
                        // entregá-lo ao content script, mas antes da execução.
                        // Revalidar aqui evita executar ações antigas.
                        const expiracao = Number(comando._expira_em || 0);
                        if (!Number.isFinite(expiracao) || expiracao <= Date.now() / 1000) {
                            throw new Error("Comando expirado; não executei a ação.");
                        }

                        retorno = await executarAcao(comando);

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

                    // Confirma a ação à ponte antes de trocar de página.
                    if (resultado.ok && retorno?.navegarDepois) {
                        const destino = retorno.navegarDepois;
                        await esperar(250);
                        location.assign(destino);
                    }
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
