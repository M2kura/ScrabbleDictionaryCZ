"""Merge sorted extractor records (stdin, sorted by form in byte order) into
the SQLite database served by server/app.py.

    words(word TEXT PRIMARY KEY, sources INT, tier INT, lemmas TEXT)

sources  bit mask over common.SOURCES (bit 0 = first letter)
tier     0 standard, 1 archaic, 2 colloquial (best tier any source gives)
lemmas   "<pos><lemma>" entries joined by "|", e.g. "Nhrad" ('' = unknown)

usage: build_db.py <output.db>
"""
import datetime
import json
import os
import sqlite3
import sys

from common import SOURCES

MAX_LEMMAS = 4
LEMMA_PRIORITY = "MHCED"  # whose analysis to show first
BATCH = 50000


def pick_lemmas(form, candidates):
    """candidates: [(source, pos, lemma)] -> up to MAX_LEMMAS (pos, lemma),
    all from the most trusted source that analysed the form."""
    if not candidates:
        return []
    best = min(LEMMA_PRIORITY.index(c[0]) for c in candidates)
    candidates = [c for c in candidates if LEMMA_PRIORITY.index(c[0]) == best]
    candidates.sort(key=lambda c: c[2] != form)
    out = []
    for _, pos, lemma in candidates:
        if (pos, lemma) in out:
            continue
        # an unknown POS ('-') is only kept when nothing better exists
        if pos == "-" and any(l == lemma for _, l in out):
            continue
        out.append((pos, lemma))
        if len(out) == MAX_LEMMAS:
            break
    return out


def main():
    path = sys.argv[1]
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.executescript("""
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA page_size = 8192;
        CREATE TABLE words (
            word TEXT PRIMARY KEY,
            sources INTEGER NOT NULL,
            tier INTEGER NOT NULL,
            lemmas TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    stats = {
        "words": 0,
        "by_source": {s: 0 for s in SOURCES},
        "only_source": {s: 0 for s in SOURCES},
        "by_tier": [0, 0, 0],
    }
    batch = []

    def finish(form, mask, tier, lemmas):
        lem = "|".join(pos + lemma.replace("|", " ") for pos, lemma in pick_lemmas(form, lemmas))
        batch.append((form, mask, tier, lem))
        if len(batch) >= BATCH:
            db.executemany("INSERT INTO words VALUES (?, ?, ?, ?)", batch)
            batch.clear()
        stats["words"] += 1
        stats["by_tier"][tier] += 1
        for i, s in enumerate(SOURCES):
            if mask & (1 << i):
                stats["by_source"][s] += 1
                if mask == 1 << i:
                    stats["only_source"][s] += 1

    cur, mask, tier, lemmas = None, 0, 9, []
    for line in sys.stdin:
        form, src, t, pos, lemma = line.rstrip("\n").split("\t")
        if form != cur:
            if cur is not None:
                finish(cur, mask, tier, lemmas)
            cur, mask, tier, lemmas = form, 0, 9, []
        mask |= 1 << SOURCES.index(src)
        tier = min(tier, int(t))
        if lemma:
            lemmas.append((src, pos, lemma))
    if cur is not None:
        finish(cur, mask, tier, lemmas)
    if batch:
        db.executemany("INSERT INTO words VALUES (?, ?, ?, ?)", batch)

    db.executemany("INSERT INTO meta VALUES (?, ?)", [
        ("version", datetime.date.today().isoformat()),
        ("sources", SOURCES),
        ("stats", json.dumps(stats)),
    ])
    db.commit()
    db.execute("VACUUM")
    db.close()
    os.replace(tmp, path)
    print(json.dumps(stats, indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
