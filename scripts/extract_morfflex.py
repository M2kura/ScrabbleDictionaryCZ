"""MorfFlex CZ 2.1: lemma <TAB> tag <TAB> form (127M lines, read from stdin).

Tag position 15 (variant) and lemma comments (_,a _,h ...) set the tier.
Abbreviations, word segments, foreign-phrase fragments, misspellings (_,i) and lowercase
forms of proper-noun lemmas are dropped.
"""
import re
import sys

from common import ARCHAIC, COLLOQUIAL, STANDARD, Writer

VARIANT_TIER = {
    "-": STANDARD, "1": STANDARD, "9": STANDARD,
    "2": ARCHAIC, "3": ARCHAIC, "4": ARCHAIC,
    "5": COLLOQUIAL, "6": COLLOQUIAL, "7": COLLOQUIAL, "8": COLLOQUIAL,
}
COMMENT_TIER = {
    "a": ARCHAIC,     # zastaralé
    "s": ARCHAIC,     # dříve užívaný pravopis (-isovat, -osa ...)
    "h": COLLOQUIAL,  # hovorové
    "l": COLLOQUIAL,  # slangové / lidové
    "n": COLLOQUIAL,  # nářeční
}
COMMENT_RE = re.compile(r"_,([a-z])")
LEMMA_END_RE = re.compile(r"(?<=.)(-\d+|[_`])")


def lemma_tier(lemma):
    tier = STANDARD
    for c in COMMENT_RE.findall(lemma):
        if c == "i":  # chybný pravopis
            return None
        tier = max(tier, COMMENT_TIER.get(c, STANDARD))
    return tier


def main():
    w = Writer("M")
    cur_lemma, cur_tier, cur_base, seen = None, None, "", set()
    for line in sys.stdin:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        lemma, tag, form = parts
        if lemma != cur_lemma:
            cur_lemma, seen = lemma, set()
            cur_tier = lemma_tier(lemma)
            cur_base = LEMMA_END_RE.split(lemma, 1)[0]
        if cur_tier is None or tag[0] in "BFSZX" or not form.islower():
            continue
        if cur_base[:1].isupper():
            continue
        vt = VARIANT_TIER.get(tag[14])
        if vt is None:  # a, b, c = zkratky
            continue
        tier = max(cur_tier, vt)
        key = (form, tier, tag[0])
        if key in seen:
            continue
        seen.add(key)
        w.emit(form, tier, tag[0], cur_base)
    w.done()


if __name__ == "__main__":
    main()
