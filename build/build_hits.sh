#!/bin/sh

BUILD_SPECIFICATION=
BIN_DIRECTORY=./bin	

##############################################
# GETOPT PARSING
##############################################

while getopts ":s:b:h" opt; do
  case $opt in
    h)
			echo "Usage: "$0" [options]"
			echo ""
			echo "Options:"
			echo "  -h show this help massage and exit"
			echo "  -s BUILDSPEC  Angabe der 'build-specification' (XML)"
			echo "  -b DIRECTORY  Angabe des Verzeichnisses für die Binary (Default ist './bin')"
      ;;
    s)
			BUILD_SPECIFICATION=$OPTARG
      ;;
    b)
			BIN_DIRECTORY=$OPTARG
      ;;
    \?)
      echo "): invalid option: -$OPTARG" >&2
			exit 1
      ;;
    :)
      echo "): the option -$OPTARG requires an argument" >&2
      exit 1
      ;;
  esac
done

##############################################
# ARGUMENT CHECKING
##############################################

if [ -z "$BUILD_SPECIFICATION" ]
then
	echo "): 'build-specification' is missing (XML)"
	exit 1
fi

if [ ! -r "$BUILD_SPECIFICATION" ]
then
	echo "): the 'build-specification' is not readable ($BUILD_SPECIFICATION)"
	exit 1
fi
if [ ! -r "$BIN_DIRECTORY/concordances" ]
then
	echo "): the binary is not readable (in $BIN_DIRECTORY)"
	exit 1
fi

##############################################
# PROCESSING
##############################################

echo "(: score sentences ..."
echo ""

$BIN_DIRECTORY/score_examples $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/score_examples' ended with error(s)"
	exit 1
fi

echo "(: create concordances ..."
echo ""

$BIN_DIRECTORY/concordances $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/concordances' ended with error(s)"
	exit 1
fi

echo ""
echo "(: done"


