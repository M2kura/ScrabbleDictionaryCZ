"""Czech Scrabble dictionary: JSON API over data/scrabble.db plus the static UI.

GET /api/lookup?q=slovo [další slova]   up to 12 words, see lookup()
GET /api/stats                          word counts and build date
GET /*                                  files from ../site

Standard library only. Env: DB_PATH, SITE_DIR, PORT.
"""
import json
import os
import re
import sqlite3
import threading
import unicodedata
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(HERE, "..", "data", "scrabble.db"))
SITE_DIR = os.environ.get("SITE_DIR", os.path.join(HERE, "..", "site"))
PORT = int(os.environ.get("PORT", "8000"))

MAX_WORDS = 12
WORD_RE = re.compile(r"^[a-záčďéěíňóřšťúůýž]+$")
ACCENTS = {
    "a": "aá", "c": "cč", "d": "dď", "e": "eéě", "i": "ií", "n": "nň", "o": "oó",
    "r": "rř", "s": "sš", "t": "tť", "u": "uúů", "y": "yý", "z": "zž",
}
STRIP = {ch: base for base, all_ in ACCENTS.items() for ch in all_}
MAX_VARIANTS = 4096

_local = threading.local()


def db():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True)
        _local.conn = conn
    return conn


def load_meta():
    rows = dict(db().execute("SELECT key, value FROM meta"))
    return rows["sources"], {"version": rows["version"], **json.loads(rows["stats"])}


SOURCES, STATS = load_meta()


def problem(word):
    if not WORD_RE.match(word):
        return "Obsahuje znak, který v české sadě kamenů není."
    if len(word) < 2:
        return "Slovo musí mít aspoň 2 písmena."
    if len(word) > 15:
        return "Slovo může mít nejvýš 15 písmen, víc se na desku nevejde."
    return None


def neighbours(word):
    c = db()
    before = [r[0] for r in c.execute(
        "SELECT word FROM words WHERE word < ? ORDER BY word DESC LIMIT 3", (word,))]
    after = [r[0] for r in c.execute(
        "SELECT word FROM words WHERE word > ? ORDER BY word LIMIT 3", (word,))]
    return before[::-1] + after


def suggest(word):
    """Existing words that differ from `word` only in diacritics."""
    variants = [""]
    for ch in word:
        opts = ACCENTS.get(STRIP.get(ch, ch), ch)
        variants = [v + o for v in variants for o in opts]
        if len(variants) > MAX_VARIANTS:
            return []
    variants = [v for v in variants if v != word]
    hits = []
    c = db()
    for i in range(0, len(variants), 500):
        chunk = variants[i:i + 500]
        hits += c.execute(
            f"SELECT word, tier FROM words WHERE word IN ({','.join('?' * len(chunk))})", chunk
        ).fetchall()
    hits.sort(key=lambda h: (h[1], h[0]))
    return [{"word": w, "tier": t} for w, t in hits[:8]]


def lookup(word):
    p = problem(word)
    if p:
        return {"word": word, "found": False, "problem": p, "neighbours": []}
    row = db().execute("SELECT sources, tier, lemmas FROM words WHERE word = ?", (word,)).fetchone()
    result = {"word": word, "found": row is not None, "neighbours": neighbours(word)}
    if row:
        mask, tier, lemmas = row
        result.update(
            tier=tier,
            sources=[s for i, s in enumerate(SOURCES) if mask & (1 << i)],
            lemmas=[{"pos": e[0], "lemma": e[1:]} for e in lemmas.split("|") if e],
        )
    else:
        result["suggestions"] = suggest(word)
    return result


def parse_words(q):
    q = unicodedata.normalize("NFC", q).lower()
    return [w for w in re.split(r"[\s,;]+", q) if w][:MAX_WORDS]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # http.server decodes the request line as Latin-1; undo that for raw UTF-8.
        url = urlsplit(self.path.encode("latin-1").decode("utf-8", "replace"))
        if url.path == "/api/lookup":
            q = parse_qs(url.query).get("q", [""])[0]
            self.send_json({"results": [lookup(w) for w in parse_words(q)]})
        elif url.path == "/api/stats":
            self.send_json(STATS)
        elif url.path.startswith("/api/"):
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        else:
            super().do_GET()

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    print(f"Serving {STATS['words']} words from {DB_PATH} on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
