#!/bin/bash
set -x

for corpus in "$@"
do
    bzcat ~/data/new_wp_conll/${corpus}.conll.bz2 | \
    python3.7 scripts/parse.py --nthreads 8 > ~/data/corpora_2023/${corpus}.conll &
done

#for corpus in "$@"
#do
#    fname=`basename ${corpus} .bz2`
#    dname=`dirname ${corpus}`
#    echo "Process corpus: ${corpus}..."
#    python3 cli/combine.py ${corpus} ${dname}/../conll-tabs/${fname}.bz2 | gzip > ${dname}/${fname}.gz &
#done
