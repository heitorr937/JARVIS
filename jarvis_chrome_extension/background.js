
const BASE = "http://127.0.0.1:8765";

async function requisicao(caminho, dados = null) {
    const opcoes = dados === null
        ? { method: "GET" }
        : {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(dados)
        };

    const resposta = await fetch(BASE + caminho, opcoes);

    if (!resposta.ok) {
        throw new Error("Erro HTTP " + resposta.status);
    }

    return await resposta.json();
}

chrome.runtime.onMessage.addListener(
    (mensagem, remetente, responder) => {

        (async () => {
            try {
                let resultado;

                switch (mensagem.tipo) {
                    case "JARVIS_SNAPSHOT":
                        resultado = await requisicao(
                            "/snapshot",
                            mensagem.dados
                        );
                        break;

                    case "JARVIS_PROXIMO":
                        resultado = await requisicao("/next");
                        break;

                    case "JARVIS_RESULTADO":
                        resultado = await requisicao(
                            "/resultado",
                            mensagem.dados
                        );
                        break;

                    default:
                        responder({
                            ok: false,
                            erro: "Mensagem desconhecida."
                        });
                        return;
                }

                responder({
                    ok: true,
                    resultado
                });

            } catch (erro) {
                console.error("Erro na ponte JARVIS:", erro);

                responder({
                    ok: false,
                    erro: erro.message || String(erro)
                });
            }
        })();

        return true;
    }
);

console.log("Ponte de comunicação do JARVIS carregada.");
