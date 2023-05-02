#!/bin/bash
set -x

for corpus in "$@"
do
    bzcat ~/data/new_wp_conll/${corpus}.conll.bz2 | \
    python3.7 scripts/parse.py -c ~/corpora/${corpus}.conll --nthreads 6 > ~/data/corpora_2023/${corpus}.conll &
done

