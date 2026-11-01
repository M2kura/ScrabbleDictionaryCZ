"""Wiktionary (wiktextract JSONL, English or Czech edition): headwords and
all forms from the inflection tables of Czech entries.

usage: extract_wiktionary.py <file.jsonl[.gz]> <source letter>
"""
import gzip
import json
import sys

from common import ARCHAIC, COLLOQUIAL, STANDARD, Writer

POS = {
    "noun": "N", "verb": "V", "adj": "A", "adv": "D", "pron": "P", "det": "P",
    "num": "C", "prep": "R", "conj": "J", "intj": "I", "particle": "T",
}
ARCHAIC_TAGS = {"archaic", "obsolete", "dated", "outdated", "Old-Cezch", "historical"}
COLLOQUIAL_TAGS = {
    "colloquial", "colloquially", "informal", "dialectal", "regional", "slang",
    "criminal-slang", "Moravia", "Bohemia", "Prague",
}
SKIP_FORM_TAGS = {"table-tags", "inflection-template", "class", "romanization", "abbreviation"}


def tags_tier(tags):
    tags = set(tags)
    if tags & COLLOQUIAL_TAGS:
        return COLLOQUIAL
    if tags & ARCHAIC_TAGS:
        return ARCHAIC
    return STANDARD


def main():
    path, source = sys.argv[1], sys.argv[2]
    f = gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")
    w = Writer(source)
    for line in f:
        d = json.loads(line)
        if d.get("lang_code") != "cs":
            continue
        pos = POS.get(d.get("pos"))
        word = d.get("word", "")
        if pos is None or not word.islower():
            continue
        senses = d.get("senses") or [{}]
        # The entry is only as "bad" as its best sense.
        tier = min(tags_tier(s.get("tags", [])) for s in senses)
        lemma = word
        for s in senses:
            fo = s.get("form_of") or s.get("alt_of")
            if fo and fo[0].get("word"):
                lemma = fo[0]["word"]
                break
        w.emit(word, tier, pos, lemma)
        for form in d.get("forms", []):
            tags = form.get("tags", [])
            if SKIP_FORM_TAGS.intersection(tags):
                continue
            text = form.get("form", "")
            if not text.islower():
                continue
            w.emit(text, max(tier, tags_tier(tags)), pos, word)
    w.done()


if __name__ == "__main__":
    main()
