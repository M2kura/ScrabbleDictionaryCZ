#!/usr/bin/env bash
# Downloads all source dictionaries into data/raw/<source>/.
set -euo pipefail
cd "$(dirname "$0")/.."
RAW=data/raw
UA='ScrabbleDictionaryCZ-build/1.0'

fetch() { # url dest
  if [[ -s "$2" ]]; then echo "skip $2"; return; fi
  mkdir -p "$(dirname "$2")"
  echo "get  $2"
  curl -fL --retry 3 -A "$UA" -o "$2.part" "$1" && mv "$2.part" "$2"
}

# MorfFlex CZ 2.1 (ÚFAL MFF UK, CC BY-NC-SA 4.0) – http://hdl.handle.net/11234/1-5833
fetch https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/cc940076-7bf0-449b-81a4-5e10e023084e/content \
  $RAW/morfflex/czech-morfflex-2.1.tsv.xz

# Hunspell cs_CZ from LibreOffice dictionaries (GPL)
for f in cs_CZ.aff cs_CZ.dic README_cs.txt; do
  fetch https://raw.githubusercontent.com/LibreOffice/dictionaries/master/cs_CZ/$f $RAW/hunspell/$f
done

# English Wiktionary, Czech entries (wiktextract / kaikki.org, CC BY-SA 4.0)
fetch https://kaikki.org/dictionary/Czech/kaikki.org-dictionary-Czech.jsonl $RAW/wiktionary/czech.jsonl

# Czech Wiktionary (wiktextract / kaikki.org, CC BY-SA 4.0)
fetch https://kaikki.org/cswiktionary/raw-wiktextract-data.jsonl.gz $RAW/cswiktionary/raw.jsonl.gz

# Wikidata lexemes in Czech (CC0)
if [[ ! -s $RAW/wikidata/lexemes.tsv ]]; then
  mkdir -p $RAW/wikidata
  echo "get  $RAW/wikidata/lexemes.tsv"
  curl -fsG --retry 3 -A "$UA" https://query.wikidata.org/sparql \
    -H 'Accept: text/tab-separated-values' \
    --data-urlencode 'query=SELECT ?form ?lemma ?cat WHERE {
      ?l dct:language wd:Q9056 ; wikibase:lemma ?lemma ; wikibase:lexicalCategory ?cat ;
         ontolex:lexicalForm/ontolex:representation ?form . }' \
    -o $RAW/wikidata/lexemes.tsv.part && mv $RAW/wikidata/lexemes.tsv.part $RAW/wikidata/lexemes.tsv
fi
