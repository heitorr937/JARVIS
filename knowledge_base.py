import html
from html.parser import HTMLParser
import ipaddress
import json
import os
import re
import socket
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.parse import quote_plus, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener
)
import xml.etree.ElementTree as ET


DATA_DIRECTORY = os.environ.get(
    "JARVIS_DATA_DIR",
    os.path.dirname(os.path.abspath(__file__))
)
DATABASE_PATH = os.path.join(DATA_DIRECTORY, "jarvis_knowledge.db")

SITE_GUIDES = (
    {
        "site_key": "geekie_one",
        "domain": "one.geekie.com.br",
        "title": "Geekie One",
        "guide": (
            "Geekie One é uma plataforma educacional com materiais e "
            "atividades interativas. O fluxo provável do estudante é abrir "
            "Atividades ou Minha Semana, escolher a tarefa e responder a "
            "questão visível. Em múltipla escolha, clicar na alternativa; "
            "em questão escrita, preencher o campo de resposta. Entregar é "
            "uma etapa separada e só deve ser feita se o usuário pedir. "
            "A organização e os rótulos podem variar por escola e conta; "
            "use a tela atual como fonte principal."
        ),
        "source_url": "https://www.geekie.com.br/geekie-one/",
        "confidence": "official_overview"
    },
    {
        "site_key": "whatsapp_web",
        "domain": "web.whatsapp.com",
        "title": "WhatsApp Web",
        "guide": (
            "Use o endereço oficial web.whatsapp.com. A sessão pode exigir "
            "que a conta seja vinculada/autenticada pelo próprio usuário. "
            "Para enviar uma mensagem, pesquise e abra o contato correto, "
            "confira a conversa, preencha a caixa de mensagem com o texto "
            "pedido e use o botão de envio visível. Não presuma que uma "
            "página de login seja uma conversa."
        ),
        "source_url": "https://web.whatsapp.com/",
        "confidence": "official_entry_point"
    },
    {
        "site_key": "spotify",
        "domain": "open.spotify.com",
        "title": "Spotify",
        "guide": (
            "No Spotify Web Player, use a busca para localizar artista, "
            "faixa, álbum ou playlist; abra o resultado correto e acione "
            "Reproduzir. A ajuda oficial documenta filtros de busca como "
            "year:, genre:, label:, track:, album:, artist: e tag:. "
            "Para procurar uma música pela letra, a ajuda recomenda usar "
            "pelo menos três palavras da letra."
        ),
        "source_url": "https://support.spotify.com/br-pt/article/search/",
        "confidence": "official_help"
    },
    {
        "site_key": "tiktok",
        "domain": "www.tiktok.com",
        "title": "TikTok",
        "guide": (
            "Na versão web do TikTok, observe a tela atual para identificar "
            "feed, busca, perfis e controles de reprodução. Rolar para baixo "
            "avança o feed; pesquisar deve usar o campo e os resultados "
            "visíveis. A interface e os recursos podem variar por região, "
            "sessão e versão."
        ),
        "source_url": "https://support.tiktok.com/en/using-tiktok/exploring-videos",
        "confidence": "official_help_entry"
    },
    {
        "site_key": "youtube",
        "domain": "www.youtube.com",
        "title": "YouTube",
        "guide": (
            "Pesquise pelo título, tema ou canal e escolha o resultado "
            "correto antes de reproduzir. A ajuda oficial informa que os "
            "filtros de busca podem separar vídeos, Shorts, filmes, "
            "playlists e canais. A classificação considera a correspondência "
            "com a busca e o engajamento; não assuma que o primeiro resultado "
            "seja sempre o mais visto."
        ),
        "source_url": "https://support.google.com/youtube/answer/111997?hl=pt-BR",
        "confidence": "official_help"
    },
    {
        "site_key": "instagram",
        "domain": "www.instagram.com",
        "title": "Instagram",
        "guide": (
            "A interface web pode variar com o estado da sessão. Use os "
            "rótulos visíveis para localizar busca, perfis, mensagens e "
            "publicações; confirme visualmente o destino antes de interagir. "
            "Este guia é orientação geral, não documentação de todos os "
            "recursos do Instagram."
        ),
        "source_url": "https://www.instagram.com/",
        "confidence": "official_entry_point"
    },
    {
        "site_key": "discord",
        "domain": "discord.com",
        "title": "Discord",
        "guide": (
            "Na versão web do Discord, observe a interface autenticada para "
            "localizar servidores, canais, busca e caixa de mensagem. Use o "
            "canal e o destinatário que o usuário indicar e confira o "
            "conteúdo antes de enviar."
        ),
        "source_url": "https://discord.com/app",
        "confidence": "official_entry_point"
    }
)


class _TextExtractor(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.title_parts = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg", "nav", "footer"):
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg", "nav", "footer"):
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in ("p", "div", "li", "br", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if not self._skip_depth:
            text = data.strip()
            if text:
                self.parts.append(text)


class _SafeRedirectHandler(HTTPRedirectHandler):

    def redirect_request(self, request, response, code, message, headers, url):
        _validate_public_url(url)
        return super().redirect_request(
            request,
            response,
            code,
            message,
            headers,
            url
        )


def _connect(database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def _database(database_path):
    connection = _connect(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path=DATABASE_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
    with _database(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS site_guides (
                id INTEGER PRIMARY KEY,
                site_key TEXT NOT NULL,
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                guide TEXT NOT NULL,
                source_url TEXT NOT NULL,
                confidence TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(site_key, source_url)
            );
            CREATE INDEX IF NOT EXISTS idx_site_guides_domain
                ON site_guides(domain);

            CREATE TABLE IF NOT EXISTS research_records (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                query_key TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_research_query_date
                ON research_records(query_key, created_at DESC);

            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY,
                research_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY(research_id)
                    REFERENCES research_records(id) ON DELETE CASCADE,
                UNIQUE(research_id, url)
            );

            CREATE TABLE IF NOT EXISTS site_workflows (
                id INTEGER PRIMARY KEY,
                site_key TEXT NOT NULL,
                goal TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                completed_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(site_key, goal)
            );
            """
        )
        now = datetime.now(timezone.utc).isoformat()
        connection.executemany(
            """
            INSERT OR IGNORE INTO site_guides
                (site_key, domain, title, guide, source_url, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    guide["site_key"],
                    guide["domain"],
                    guide["title"],
                    guide["guide"],
                    guide["source_url"],
                    guide["confidence"],
                    now
                )
                for guide in SITE_GUIDES
            ]
        )


def _normalize_query(query):
    return re.sub(r"\s+", " ", query.casefold()).strip()


def _tokens(text):
    return {
        token for token in re.findall(r"[a-z0-9áàâãéêíóôõúç]{3,}", text.casefold())
        if token not in {
            "para", "com", "uma", "que", "the", "and", "site", "sobre"
        }
    }


def relevant_guidance(query, database_path=DATABASE_PATH, limit=5):
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    with _database(database_path) as connection:
        guides = connection.execute(
            "SELECT site_key, domain, title, guide, source_url, confidence "
            "FROM site_guides"
        ).fetchall()
        workflows = connection.execute(
            "SELECT site_key, goal, steps_json, completed_count "
            "FROM site_workflows"
        ).fetchall()

    matches = []
    for guide in guides:
        searchable = " ".join(
            (guide["site_key"], guide["domain"], guide["title"])
        )
        overlap = query_tokens & _tokens(searchable)
        if overlap:
            matches.append(
                (
                    len(overlap),
                    {
                        "kind": "guide",
                        "site_key": guide["site_key"],
                        "title": guide["title"],
                        "content": guide["guide"],
                        "source_url": guide["source_url"],
                        "confidence": guide["confidence"]
                    }
                )
            )

    for workflow in workflows:
        searchable = workflow["site_key"] + " " + workflow["goal"]
        overlap = query_tokens & _tokens(searchable)
        if overlap:
            matches.append(
                (
                    len(overlap) + 1,
                    {
                        "kind": "workflow",
                        "site_key": workflow["site_key"],
                        "title": workflow["goal"],
                        "content": (
                            "Fluxo local concluído "
                            f"{workflow['completed_count']} vez(es): "
                            + " -> ".join(json.loads(workflow["steps_json"]))
                        ),
                        "source_url": "base local de observações",
                        "confidence": "observed"
                    }
                )
            )

    matches.sort(key=lambda result: result[0], reverse=True)
    return [result[1] for result in matches[:limit]]


def save_research(query, answer, sources, database_path=DATABASE_PATH):
    created_at = datetime.now(timezone.utc).isoformat()
    query_key = _normalize_query(query)
    with _database(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO research_records "
            "(query, query_key, answer, created_at) VALUES (?, ?, ?, ?)",
            (query.strip(), query_key, answer.strip(), created_at)
        )
        research_id = cursor.lastrowid
        connection.executemany(
            "INSERT OR IGNORE INTO research_sources "
            "(research_id, title, url) VALUES (?, ?, ?)",
            [
                (
                    research_id,
                    str(source.get("title", "Fonte"))[:300],
                    str(source["url"])[:2000]
                )
                for source in sources
                if isinstance(source, dict) and source.get("url")
            ]
        )
    return research_id


def cached_research(query, database_path=DATABASE_PATH, max_age_hours=24):
    cutoff = (
        datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    ).isoformat()
    with _database(database_path) as connection:
        record = connection.execute(
            "SELECT id, answer, created_at FROM research_records "
            "WHERE query_key = ? AND created_at >= ? "
            "ORDER BY created_at DESC LIMIT 1",
            (_normalize_query(query), cutoff)
        ).fetchone()
        if not record:
            return None

        sources = connection.execute(
            "SELECT title, url FROM research_sources "
            "WHERE research_id = ? ORDER BY id",
            (record["id"],)
        ).fetchall()
    return {
        "answer": record["answer"],
        "sources": [dict(source) for source in sources],
        "created_at": record["created_at"]
    }


def _validate_public_url(url):
    parts = urlsplit(url)
    hostname = parts.hostname
    if (
        parts.scheme not in ("http", "https")
        or not hostname
        or parts.username
        or parts.password
        or parts.port
    ):
        raise ValueError("A fonte retornou um endereço web inválido.")

    if hostname.casefold() == "localhost" or hostname.casefold().endswith(
        (".localhost", ".local")
    ):
        raise ValueError("Não permito acessar endereços locais.")

    try:
        addresses = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    hostname,
                    parts.port or (443 if parts.scheme == "https" else 80),
                    type=socket.SOCK_STREAM
                )
            ]
        except OSError as erro:
            raise ValueError("Não consegui validar o endereço da fonte.") from erro

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("A fonte apontou para um endereço de rede não público.")
    return parts.geturl()


def _fetch_page(url, max_bytes=750_000, timeout=10):
    safe_url = _validate_public_url(url)
    opener = build_opener(_SafeRedirectHandler())
    request = Request(
        safe_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            ),
            "Accept": "text/html,text/plain;q=0.8"
        }
    )
    with opener.open(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "").casefold()
        if not any(
            allowed in content_type
            for allowed in ("text/html", "text/plain", "application/xhtml")
        ):
            return "", ""
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        charset = response.headers.get_content_charset() or "utf-8"

    decoded = raw.decode(charset, errors="replace")
    parser = _TextExtractor()
    parser.feed(decoded)
    title = re.sub(r"\s+", " ", " ".join(parser.title_parts)).strip()
    text = html.unescape(" ".join(parser.parts))
    text = re.sub(r"\s+", " ", text).strip()
    return title, text[:9000]


def search_and_fetch(query, limit=4):
    search_url = (
        "https://www.bing.com/search?format=rss&q="
        + quote_plus(query)
    )
    _validate_public_url(search_url)
    request = Request(
        search_url,
        headers={"User-Agent": "JARVIS-local-assistant/1.0"}
    )
    opener = build_opener(_SafeRedirectHandler())
    with opener.open(request, timeout=12) as response:
        payload = response.read(500_000)

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as erro:
        raise RuntimeError(
            "O serviço de pesquisa não retornou resultados legíveis."
        ) from erro

    items = root.findall("./channel/item")
    if not items:
        raise RuntimeError(
            "Não encontrei resultados. Tente reformular a pesquisa."
        )

    sources = []
    for item in items:
        if len(sources) >= limit:
            break
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        if not title or not url:
            continue
        try:
            safe_url = _validate_public_url(url)
            page_title, content = _fetch_page(safe_url)
        except (OSError, URLError, ValueError, RuntimeError):
            continue
        if content:
            title = page_title or title
        sources.append({
            "title": title[:300],
            "url": safe_url,
            "content": content
        })

    if not sources:
        raise RuntimeError(
            "Encontrei resultados, mas não consegui acessar fontes "
            "públicas legíveis."
        )
    return sources


def workflow_site_key(request, active_title=""):
    text = (request + " " + active_title).casefold()
    aliases = {
        "geekie_one": ("geekie", "geeki", "gennini", "genni"),
        "whatsapp_web": ("whatsapp", "wahtsapp", "watsapp"),
        "spotify": ("spotify",),
        "tiktok": ("tiktok",),
        "youtube": ("youtube",),
        "instagram": ("instagram",),
        "discord": ("discord",)
    }
    for site_key, names in aliases.items():
        if any(name in text for name in names):
            return site_key
    return "other"


def workflow_goal(request):
    patterns = (
        ("messaging", r"\b(mensagem|mensagens|enviar|envie|contato)\b"),
        ("media_search", r"\b(pesquise|pesquisar|buscar|busque|música|musica|vídeo|video)\b"),
        ("media_playback", r"\b(tocar|reproduzir|reproduza|play|pausar|pause)\b"),
        ("school_activity", r"\b(geekie|atividade|questão|questao|tarefa|dever)\b"),
        ("navigation", r"\b(abrir|abra|acessar|acesse|entre|entrar|clique)\b")
    )
    for goal, pattern in patterns:
        if re.search(pattern, request, re.IGNORECASE):
            return goal
    return "general_control"


def _action_category(action):
    description = (
        action.get("description", "") + " "
        + action.get("target_label", "")
    ).casefold()
    if action.get("type") == "scroll":
        return "scroll"
    if action.get("type") == "type":
        return "fill_field"
    if action.get("type") == "press":
        return "keyboard"
    categories = (
        ("submit", r"\b(entregar|entrega|enviar|envia|submit|finish)\b"),
        ("answer_choice", r"\b(alternativa|opção|opcao|choice|option)\b"),
        ("search", r"\b(busca|pesquisa|search)\b"),
        ("playback", r"\b(reproduzir|play|pausar|pause|tocar)\b"),
        ("contact", r"\b(contato|conversa|chat)\b"),
        ("navigation", r"\b(aba|menu|link|atividade|página|pagina)\b")
    )
    for category, pattern in categories:
        if re.search(pattern, description):
            return category
    return "click"


def save_workflow(request, actions, completed, active_title="", database_path=DATABASE_PATH):
    if not actions:
        return
    site_key = workflow_site_key(request, active_title)
    goal = workflow_goal(request)
    steps = [_action_category(action) for action in actions]
    timestamp = datetime.now(timezone.utc).isoformat()

    with _database(database_path) as connection:
        row = connection.execute(
            "SELECT steps_json, completed_count FROM site_workflows "
            "WHERE site_key = ? AND goal = ?",
            (site_key, goal)
        ).fetchone()
        previous = json.loads(row["steps_json"]) if row else []
        merged_steps = list(dict.fromkeys(previous + steps))
        completed_count = (row["completed_count"] if row else 0)
        completed_count += 1 if completed else 0
        connection.execute(
            """
            INSERT INTO site_workflows
                (site_key, goal, steps_json, completed_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(site_key, goal) DO UPDATE SET
                steps_json = excluded.steps_json,
                completed_count = excluded.completed_count,
                completed_count = excluded.completed_count,
                updated_at = excluded.updated_at
            """,
            (
                site_key,
                goal,
                json.dumps(merged_steps),
                completed_count,
                timestamp
            )
        )


def list_database_stats(database_path=DATABASE_PATH):
    with _database(database_path) as connection:
        return {
            "site_guides": connection.execute(
                "SELECT COUNT(*) FROM site_guides"
            ).fetchone()[0],
            "research_records": connection.execute(
                "SELECT COUNT(*) FROM research_records"
            ).fetchone()[0],
            "site_workflows": connection.execute(
                "SELECT COUNT(*) FROM site_workflows"
            ).fetchone()[0]
        }
