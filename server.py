#!/usr/bin/env python3
"""
Hard Tech News Aggregator

Fetches the latest news from hard tech, deep tech, and frontier technology
sources every time you open it.

Usage:
    python server.py

Opens a browser with the latest hard tech news from across the web.
Uses only Python standard library - no dependencies required.
"""

import http.server
import json
import re
import socket
import ssl
import threading
import webbrowser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

# ── Configuration ──────────────────────────────────────────────────────────────

HOST = "127.0.0.1"
FETCH_TIMEOUT = 15
MAX_WORKERS = 16
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# ── Feed Sources ───────────────────────────────────────────────────────────────


def _gn(query):
    """Build a Google News RSS URL for the last 7 days."""
    q = quote(query)
    return f"https://news.google.com/rss/search?q={q}+when:7d&hl=en-US&gl=US&ceid=US:en"


# Categories and their RSS feed URLs, inspired by topics from
# hardstartups.substack.com: hard tech company building, deep tech,
# manufacturing, defense, energy, robotics, semiconductors, biotech, space.
CATEGORY_FEEDS = {
    "Hard Tech": [
        _gn('"hard tech" startup'),
        _gn('"deep tech" startup funding'),
        _gn("hardtech deeptech venture capital"),
    ],
    "Defense & Aerospace": [
        _gn("defense tech startup funding"),
        _gn("defense technology military startup"),
        _gn("Anduril OR Palantir OR Shield AI defense"),
    ],
    "Energy & Nuclear": [
        _gn("nuclear fusion startup"),
        _gn("nuclear energy small modular reactor"),
        _gn("clean energy climate tech startup funding"),
    ],
    "Robotics": [
        _gn("robotics startup funding"),
        _gn("humanoid robot startup"),
        _gn("industrial automation robotics"),
    ],
    "Semiconductors": [
        _gn("semiconductor chip startup"),
        _gn("chip manufacturing startup funding"),
    ],
    "Biotech": [
        _gn("biotech startup funding"),
        _gn("synthetic biology gene therapy startup"),
    ],
    "Space": [
        _gn("space technology startup"),
        _gn("satellite launch startup funding"),
        "https://spacenews.com/feed/",
    ],
    "Manufacturing": [
        _gn('"advanced manufacturing" startup'),
        _gn("3D printing additive manufacturing startup"),
    ],
    "Quantum & Computing": [
        _gn("quantum computing startup"),
        _gn("photonics computing startup"),
    ],
}

# Curated publication RSS feeds for broader hard tech coverage
PUBLICATION_FEEDS = [
    ("TechCrunch", "https://techcrunch.com/category/hardware/feed/"),
    ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/science"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
]

# ── RSS Parser ─────────────────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_RE = re.compile(r"&[a-zA-Z]+;")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text):
    """Remove HTML tags and entities from text."""
    text = _HTML_TAG_RE.sub("", text)
    text = _HTML_ENTITY_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def _el_text(parent, tag, ns=None):
    """Get text of a child element, or None."""
    child = parent.find(tag, ns) if ns else parent.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def _parse_date(date_str):
    """Try to parse an RSS date string to ISO format."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str).isoformat()
    except Exception:
        return date_str


def _parse_rss_item(item):
    """Parse an RSS 2.0 <item> into an article dict."""
    title = _el_text(item, "title")
    link = _el_text(item, "link")
    if not title or not link:
        return None

    desc = _strip_html(_el_text(item, "description") or "")
    if len(desc) > 300:
        desc = desc[:297] + "..."

    source_el = item.find("source")
    source = ""
    if source_el is not None and source_el.text:
        source = source_el.text.strip()

    return {
        "title": title,
        "link": link,
        "description": desc,
        "date": _parse_date(_el_text(item, "pubDate")),
        "source": source,
    }


def _parse_atom_entry(entry, ns):
    """Parse an Atom <entry> into an article dict."""
    title = _el_text(entry, "atom:title", ns)
    link_el = entry.find("atom:link[@rel='alternate']", ns)
    if link_el is None:
        link_el = entry.find("atom:link", ns)
    link = link_el.get("href") if link_el is not None else None
    if not title or not link:
        return None

    desc = _strip_html(
        _el_text(entry, "atom:summary", ns)
        or _el_text(entry, "atom:content", ns)
        or ""
    )
    if len(desc) > 300:
        desc = desc[:297] + "..."

    date = _el_text(entry, "atom:updated", ns) or _el_text(
        entry, "atom:published", ns
    )

    return {
        "title": title,
        "link": link,
        "description": desc,
        "date": date,
        "source": "",
    }


def fetch_feed(url):
    """Fetch and parse one RSS/Atom feed URL. Returns list of article dicts."""
    articles = []
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(req, timeout=FETCH_TIMEOUT, context=ctx) as resp:
            data = resp.read()
        root = ET.fromstring(data)

        # RSS 2.0
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item"):
                a = _parse_rss_item(item)
                if a:
                    articles.append(a)

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            a = _parse_atom_entry(entry, ns)
            if a:
                articles.append(a)

    except Exception:
        pass  # silently skip failed feeds

    return articles


# ── Aggregation ────────────────────────────────────────────────────────────────


def fetch_all_news():
    """Fetch all feeds in parallel. Returns {category: [articles]}."""
    results = {}
    all_articles = []
    seen = set()

    # Build (category, url) task list
    tasks = []
    for cat, urls in CATEGORY_FEEDS.items():
        for url in urls:
            tasks.append((cat, url))
    for name, url in PUBLICATION_FEEDS:
        tasks.append(("Publications", url))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {
            pool.submit(fetch_feed, url): (cat, url) for cat, url in tasks
        }
        for future in as_completed(future_map):
            cat, _ = future_map[future]
            try:
                for article in future.result():
                    key = article["title"].lower().strip()
                    if key in seen:
                        continue
                    seen.add(key)
                    article["category"] = cat
                    results.setdefault(cat, []).append(article)
                    all_articles.append(article)
            except Exception:
                pass

    # Sort each category newest-first
    for cat in results:
        results[cat].sort(key=lambda a: a.get("date") or "", reverse=True)
    all_articles.sort(key=lambda a: a.get("date") or "", reverse=True)
    results["All"] = all_articles

    return results


# ── HTTP Server ────────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/news":
            self._api_news()
        elif path in ("/", "/index.html"):
            self._serve_file("index.html")
        else:
            self._serve_file(path.lstrip("/"))

    def _api_news(self):
        try:
            data = fetch_all_news()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def _serve_file(self, name):
        fp = STATIC_DIR / name
        if not fp.exists() or not fp.is_file():
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(fp.suffix, "application/octet-stream"))
        self.end_headers()
        self.wfile.write(fp.read_bytes())

    def log_message(self, fmt, *args):
        pass  # suppress default logs


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def main():
    port = _free_port()
    server = http.server.HTTPServer((HOST, port), Handler)
    url = f"http://{HOST}:{port}"

    print()
    print("  Hard Tech News Aggregator")
    print("  ─────────────────────────────────")
    print(f"  Running at: {url}")
    print("  Press Ctrl+C to stop")
    print()

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
