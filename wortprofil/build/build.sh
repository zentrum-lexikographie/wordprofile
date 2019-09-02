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
			echo "  -s BUILDSPEC  Angabe der 'build-specification' (XML) (Default ist './spec/specification.xml')"
			echo "  -b DIRECTORY  Angabe des Verzeichnisses für die Binary (Default ist './bin')"
			exit 0
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

##############################################
# PROCESSING
##############################################

sh build_statistics.sh -s $BUILD_SPECIFICATION -b $BIN_DIRECTORY

sh build_hits.sh -s $BUILD_SPECIFICATION -b $BIN_DIRECTORY

