#!/usr/bin/env bash
# Full rebuild: download sources, extract, merge and write data/scrabble.db.
set -euo pipefail
cd "$(dirname "$0")/.."
RAW=data/raw WORK=data/work DB=data/scrabble.db
mkdir -p $WORK

./scripts/download.sh

python3 scripts/extract_hunspell.py $RAW/hunspell/cs_CZ.aff $RAW/hunspell/cs_CZ.dic > $WORK/hunspell.tsv
python3 scripts/extract_wiktionary.py $RAW/wiktionary/czech.jsonl E > $WORK/enwikt.tsv
python3 scripts/extract_wiktionary.py $RAW/cswiktionary/raw.jsonl.gz C > $WORK/cswikt.tsv
python3 scripts/extract_wikidata.py $RAW/wikidata/lexemes.tsv > $WORK/wikidata.tsv
xz -dc -T2 $RAW/morfflex/czech-morfflex-2.1.tsv.xz | python3 scripts/extract_morfflex.py > $WORK/morfflex.tsv

LC_ALL=C sort -u -S 3G -T $WORK \
  $WORK/morfflex.tsv $WORK/hunspell.tsv $WORK/enwikt.tsv $WORK/cswikt.tsv $WORK/wikidata.tsv \
  | python3 scripts/build_db.py $DB
du -sh $DB
