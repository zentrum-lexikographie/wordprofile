#zdl_scripts=/home/knaebel/Projects/IMS/zdl_scripts
zdl_scripts=/home/knaebel/wp2/zdl_scripts
CORPUS=/home/ddc-dstar/dstar/corpora/dradio

DYNET_SEED=14464227
IMSPARSER=$zdl_scripts/ims_parser/main.py
IMSTRANSPARSER=$zdl_scripts/imstrans_parser/ims_trans.jar
TRANS_PARSER=$zdl_scripts/models/dta_trans_parser/trans.test-model
GRAPH_PARSER=$zdl_scripts/models/dta_graph_parser/graph.test-model
IMSTRANS_PARSER=$zdl_scripts/models/ims_trans/ims_trans.dta.model

#mkdir dradio
#echo "make XML list file"
#> dradio/dradio.files.txt
#for path in $CORPUS/build/cab_corpus/corpus-cab.d/id_*.cab.t.xml
#do
#	fname=$(basename "$path" .cab.t.xml)
#	echo "$path -o dradio/$fname.tj" >> dradio/dradio.list
#done
#
#echo "shorten file list"
#head -n 100 dradio/dradio.list > dradio/dradio.short.list
#
#echo "Use DTA CAB"
#dta-cab-analyze.perl \
#    -c=/home/ddc-dstar/dstar/resources/de/cab.plm -list \
#	-jobs=16 -block=16k@s \
#    -ifc=xmltokwrapfast dradio/dradio.short.list \
#    -ofc=tj -o dradio/$fname.tj

echo "make TJ list file"
> dradio/dradio.tj.list
for path in dradio/*.tj
do
	fname=$(basename "$path" .tj)
	echo "dradio/$fname.tj dradio/$fname.conllu" >> dradio/dradio.tj.list
done
python3 $zdl_scripts/tj2conllu.py dradio/dradio.tj.list --list --jobs 16

echo "PARSE"
> dradio/dradio.conllu.list
for path in dradio/id_*[0-9].conllu
do
    echo "$path dradio/$(basename $path .conllu).trans.conllu" >> dradio/dradio.conllu.list
done
python3 $IMSPARSER \
    --dynet-devices "CPU" \
    --dynet-seed $DYNET_SEED \
    --model $TRANS_PARSER \
    --parser TRANS \
    --format conllu \
    --src dradio/dradio.conllu.list --list --jobs 8
