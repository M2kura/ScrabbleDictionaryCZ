"""Hunspell cs_CZ: expand every .dic entry with the .aff prefix/suffix rules
(including two-level suffixes and prefix cross products)."""
import re
import sys

from common import Writer


def parse_aff(path):
    rules = {}  # flag -> (kind, cross, [(strip, add, contflags, regex)])
    forbidden = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            if p[0] == "FORBIDDENWORD":
                forbidden = p[1]
            if p[0] not in ("PFX", "SFX"):
                continue
            kind, flag = p[0], p[1]
            if flag not in rules:  # header: PFX flag cross count
                rules[flag] = (kind, p[2] == "Y", [])
                continue
            strip = "" if p[2] == "0" else p[2]
            add, _, cont = p[3].partition("/")
            add = "" if add == "0" else add
            cond = p[4] if len(p) > 4 else "."
            rx = re.compile(("^" + cond) if kind == "PFX" else (cond + "$"))
            rules[flag][2].append((strip, add, cont, rx))
    return rules, forbidden


def apply(rule_list, kind, word):
    for strip, add, cont, rx in rule_list:
        if not rx.search(word):
            continue
        if kind == "SFX":
            if strip and not word.endswith(strip):
                continue
            yield word[: len(word) - len(strip)] + add, cont
        else:
            if strip and not word.startswith(strip):
                continue
            yield add + word[len(strip):], cont


def expand(word, flags, rules):
    out = {word}
    suffixed = []  # (form, cross)
    for fl in flags:
        r = rules.get(fl)
        if not r or r[0] != "SFX":
            continue
        for form, cont in apply(r[2], "SFX", word):
            out.add(form)
            suffixed.append((form, r[1]))
            for cfl in cont:  # two-level suffixes
                cr = rules.get(cfl)
                if cr and cr[0] == "SFX":
                    for f2, _ in apply(cr[2], "SFX", form):
                        out.add(f2)
                        suffixed.append((f2, r[1] and cr[1]))
    for fl in flags:
        r = rules.get(fl)
        if not r or r[0] != "PFX":
            continue
        out.update(f for f, _ in apply(r[2], "PFX", word))
        if r[1]:
            for form, cross in suffixed:
                if cross:
                    out.update(f for f, _ in apply(r[2], "PFX", form))
    return out


def main():
    aff, dic = sys.argv[1], sys.argv[2]
    rules, forbidden = parse_aff(aff)
    w = Writer("H")
    with open(dic, encoding="utf-8") as f:
        next(f)  # entry count
        for line in f:
            entry = line.strip()
            if not entry:
                continue
            word, _, flags = entry.partition("/")
            if forbidden and forbidden in flags:
                continue
            if not word[:1].islower():
                continue
            for form in expand(word, flags, rules):
                if form.islower():
                    w.emit(form, lemma=word)
    w.done()


if __name__ == "__main__":
    main()
