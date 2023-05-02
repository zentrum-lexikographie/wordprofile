set -x

WP=wp_2023
WPDIR=~/data/wordprofiles/$WP
NJOBS=4
MINFREQ=3


run() {
    fname=`basename $1 .conll`
    echo "$1 process to $WPDIR/stage/$fname"
    cat $1 | python3.7 -m wordprofile.cli.extract_collocations --dest $WPDIR/stage/$fname --njobs $NJOBS
}

rm -r $WPDIR/*
for corpus in "$@"
do
    run $corpus &
#    sleep $((10 + RANDOM % 60))
done
wait

python3.7 wordprofile/cli/compute_statistics.py $WPDIR/stage/* --dest $WPDIR/final --min-rel-freq $MINFREQ --mwe
python3.7 wordprofile/cli/load_database.py $WPDIR/final --user wpuser --db $WP
