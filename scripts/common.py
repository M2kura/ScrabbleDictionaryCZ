"""Shared helpers for the extractors.

Every extractor writes TSV records to stdout:

    form <TAB> source <TAB> tier <TAB> pos <TAB> lemma

source  one letter, see SOURCES
tier    0 = standard (spisovné), 1 = archaic / old spelling / bookish,
        2 = colloquial / dialectal / slang
pos     one letter part of speech (PDT style) or '-' when unknown
lemma   base form ('' when unknown)
"""
import re
import sys

# Order defines the bit in the final source mask (bit 0 = first).
SOURCES = "MHECD"  # MorfFlex, Hunspell, En-Wiktionary, Cs-Wiktionary, wikiData

STANDARD, ARCHAIC, COLLOQUIAL = 0, 1, 2

# Czech Scrabble has tiles for a-z (minus q, w, playable only by a blank)
# plus these accented letters, so all of them may appear in a playable word.
WORD_RE = re.compile(r"^[a-záčďéěíňóřšťúůýž]{2,15}$")


def valid_form(form):
    return WORD_RE.match(form) is not None


def clean(field):
    return field.replace("\t", " ").replace("\n", " ")


class Writer:
    def __init__(self, source, out=sys.stdout):
        assert source in SOURCES
        self.source = source
        self.out = out
        self.count = 0

    def emit(self, form, tier=STANDARD, pos="-", lemma=""):
        if not valid_form(form):
            return
        self.out.write(f"{form}\t{self.source}\t{tier}\t{pos or '-'}\t{clean(lemma)}\n")
        self.count += 1

    def done(self):
        print(f"[{self.source}] {self.count} records", file=sys.stderr)
