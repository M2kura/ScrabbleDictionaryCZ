"""Wikidata Czech lexemes (SPARQL TSV export: ?form ?lemma ?cat)."""
import sys

from common import Writer

CATEGORY = {
    "Q1084": "N", "Q24905": "V", "Q34698": "A", "Q380057": "D", "Q36224": "P",
    "Q63116": "C", "Q4833830": "R", "Q36484": "J", "Q83034": "I", "Q184943": "T",
}


def literal(s):
    # "slovo"@cs
    return s[1:s.rfind('"')] if s.startswith('"') else s


def main():
    w = Writer("D")
    with open(sys.argv[1], encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            form, lemma = literal(parts[0]), literal(parts[1])
            qid = parts[2].rstrip(">").rsplit("/", 1)[-1]
            pos = CATEGORY.get(qid)
            if pos is None or not lemma.islower():  # proper nouns, affixes, phrases ...
                continue
            w.emit(form, pos=pos, lemma=lemma)
    w.done()


if __name__ == "__main__":
    main()
