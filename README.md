# Český scrabble slovník

A web app for checking whether a word is valid in Czech Scrabble. It merges five open
Czech lexical sources into one list of **~14.2 million word forms** (all inflections, 2–15
letters). The list covers modern words, older spellings and archaic forms, as well as colloquial
forms (marked as such).

Type a word to see:

- whether it is valid under the strictness you picked (standard only / plus archaic / plus colloquial)
- which of the five dictionaries contain it (more sources = more certain)
- its base form and part of speech (*hradům → tvar slova hrad, podstatné jméno*)
- its score with official Czech tile values
- spellings that differ only in diacritics, when the typed word isn't found (*kocka → kočka*)

Several words separated by spaces are checked at once, e.g. every word formed in one move.

## Sources

| Source | Unique forms | License |
|---|---:|---|
| [MorfFlex CZ 2.1](http://hdl.handle.net/11234/1-5833) (ÚFAL MFF UK, 2024) | 13.8 M | CC BY-NC-SA 4.0 |
| [Hunspell cs_CZ](https://github.com/LibreOffice/dictionaries/tree/master/cs_CZ) (LibreOffice, updated 2021), affix-expanded | 2.8 M | GPL |
| English Wiktionary, Czech entries ([kaikki.org](https://kaikki.org/dictionary/Czech/)) | 372 k | CC BY-SA 4.0 |
| Czech Wiktionary / Wikislovník ([kaikki.org](https://kaikki.org/cswiktionary/rawdata.html)) | 316 k | CC BY-SA 4.0 |
| [Wikidata lexemes](https://www.wikidata.org/wiki/Wikidata:Lexicographical_data) (Czech) | 143 k | CC0 |

Because MorfFlex is CC BY-NC-SA, the generated database is **non-commercial,
share-alike**. Don't use it commercially without a license from ÚFAL.

### What is filtered out

- proper nouns: capitalised forms, plus lowercase forms of proper-noun lemmas
- abbreviations, word segments, and fragments of foreign phrases (MorfFlex POS `B`, `S`, `F`)
- known misspellings (MorfFlex lemma comment `_,i`)
- anything with characters outside the Czech set: a–z plus áčďéěíňóřšťúůýž. Q and W are kept,
  since they can be played with a blank.
- words shorter than 2 or longer than 15 letters

### Register (tier)

Each form gets the *best* register any source gives it:

- **spisovné (standard):** MorfFlex variant `-`, `1`, `9`, and untagged dictionary entries
- **zastaralé (archaic):** MorfFlex variant `2`–`4`; lemma comments `_,a` (archaic) and `_,s`
  (pre-1993 spelling such as *-isovat*); Wiktionary tags archaic/obsolete/dated
- **hovorové (colloquial):** MorfFlex variant `5`–`8`; comments `_,h` `_,l` `_,n`; Wiktionary
  tags colloquial/dialectal/slang

Note that MorfFlex also generates many systematic derivations, such as negated superlatives of
participles. These are grammatical but rare. When a word is found in only one source, the app
says so.

## Building the data

Requires Python 3.10+, `curl`, `xz` and GNU `sort`. It takes about 10 minutes and needs ~1.5 GB
of downloads and ~2 GB of temporary disk.

```sh
./scripts/build.sh
```

The steps are:

1. `scripts/download.sh` – fetches every source into `data/raw/` (git-ignored)
2. `scripts/extract_*.py` – one extractor per source, each writing
   `form, source, tier, pos, lemma` TSV to `data/work/`
3. `sort -u` + `scripts/build_db.py` – merges the records by form into `data/scrabble.db`
   (SQLite, ~500 MB, one `WITHOUT ROWID` table keyed by word)

## Architecture

- `server/app.py` – Python standard library only. It serves the UI from `site/` and a JSON API
  that reads the database (read-only, immutable):
  - `GET /api/lookup?q=slovo další` – up to 12 words. Each result has validity, register,
    sources, base forms, alphabetical neighbours, and diacritics suggestions when not found.
    Answers in ~1–3 ms.
  - `GET /api/stats` – word counts and build date
- `site/` – plain HTML/CSS/JS. It uses relative URLs, so it works under a path prefix.

## Running

Local, without Docker:

```sh
python3 server/app.py          # http://localhost:8000
```

Production (on the home server):

```sh
docker compose up -d --build   # 127.0.0.1:3003, the database mounted read-only
```

Caddy publishes it at https://m2kura.dev/scrabble/ (see `HomePage/deploy/Caddyfile`).
After rebuilding the database, run `docker compose restart`.
