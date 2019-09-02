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
if [ ! -r "$BIN_DIRECTORY/mapping" -o ! -r "$BIN_DIRECTORY/preprocessing" -o ! -r "$BIN_DIRECTORY/statistics" -o ! -r "$BIN_DIRECTORY/postprocessing" -o ! -r "$BIN_DIRECTORY/clean_and_sort" ]
then
	echo "): the binary is not readable (in $BIN_DIRECTORY)"
	exit 1
fi

#echo "(: check XML specification ..." 
#xmllint --noout --schema ./spec/build-specification.xsd $BUILD_SPECIFICATION 1>/dev/null 2>/dev/null
#if [ "$?" -ne 0 ]
#then
#	echo ""
#	echo "): the XML specification is not valid:"
#  xmllint --noout --schema ./spec/build-specification.xsd $BUILD_SPECIFICATION
#	exit 1
#fi

##############################################
# PROCESSING
##############################################

echo "(: process wordprofile statistics ..."
echo ""

$BIN_DIRECTORY/mapping $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/mapping' ended with error(s)"
	exit 1
fi

$BIN_DIRECTORY/preprocessing $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/preprocessing' ended with error(s)"
	exit 1
fi

$BIN_DIRECTORY/statistics $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/statistics' ended with error(s)"
	exit 1
fi

$BIN_DIRECTORY/postprocessing $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/postprocessing' ended with error(s)"
	exit 1
fi

$BIN_DIRECTORY/clean_and_sort $BUILD_SPECIFICATION
if [ "$?" -eq 255 ]
then
	echo ""
	echo "): program '$BIN_DIRECTORY/clean_and_sort' ended with error(s)"
	exit 1
fi



echo ""
echo "(: done"

