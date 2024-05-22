# Preprocessing

I [Data conversion](#I-data-conversion)
II [Annotation of Dependency Relations](#II-annotation-of-dependency-relations)

# I Data conversion
Convert ZDL-internal DDC-Dump/Tabs files to conllu format.

(Adaption of [`pytabs`](https://git.zdl.org/zdl/pytabs) project by René Knaebel.)

## Usage
### Update existing .conll data
To extend an existing collection of `.conll` files with new data, the `data_update.py` script can be used.

This script is specially tailored to the `ddc/dstar` infrastructure. It processes data in two directories: The first is the `data-root` directory where existing `.conll` data is stored. In this directory and subdirectories, basenames of documents for a `corpus` are extracted from all `corpus.toc` files present. A `.toc` file contains one basename per line. New data will be written to a subdirectory of `data-root` with the current date as name. A `corpus.conll` with the processed conll data and a `corpus.toc` file containing the basenames of the documents in the new conll file are stored in this subdirectory.

The second directory is `corpus/build/ddc_dump` that should contain a `corpus-tabs.files` file and a subdirectory `corpus-tabs.d` with `.tabs` files for `corpus`.

If no `corpus.toc` exists in data directory, this script can also be used to build a whole `.conll` corpus from scratch.

```shell script
Usage: data_update.py [OPTIONS]

  Generate .conll file for corpus from .tabs files that are not contained in
  existing data.

  Existing basenames are read from .toc files, new basenames are extracted
  from list in 'corpus-tabs.files'. New data is written to a subdirectory of
  the existing data directory, using the current date as name. A .toc file
  with the new basenames is added there as well.

Options:
  -c, --corpus TEXT               Name of corpus. Used for detection of .toc
                                  files and naming of output files.
                                  [required]

  -d, --data-root DIRECTORY       Path to directory containing existing data
                                  and .toc files. New data will be written to
                                  a subdirectory there.  [required]

  -t, --tabs-dump-path DIRECTORY  Path to 'ddc_dump' directory that contains
                                  subdir with .tabs files and 'corpus-
                                  tabs.files'.  [required]

  -h, --help                      Show this message and exit.

```

Log files are stored in a `log` directory under `preprocessing`.

#### Example of directory structure for `data-root`
Structure of the data directory with existing data.
```.
├── 2023-11-01
│   ├── corpus.conll
│   └── corpus.toc
├── corpus.conll
└── corpus.toc
```
After the data update, the directory looks like this:
```
.
├── 2023-11-01
│   ├── corpus.conll
│   └── corpus.toc
├── 2023-xx-xx
│   ├── corpus.conll
│   └── corpus.toc
├── corpus.conll
└── corpus.toc
```

### Convert single or multiple .tabs files
For conversion of one or more `.tabs` files matching a glob path, the Python script `tabs2conllu.py` can be used. The output can be printed to stdout or written to individual files for each input document.

```shell script
Usage: tabs2conllu.py [OPTIONS]

  Tabs to Conllu conversion

Options:
  -i, --input TEXT                Glob compatible path pattern for source
                                  files.
  -o, --output TEXT               Path to destination folder.
  -h, --help                      Show this message and exit.

```

If the `--output` option is used, the `.conll` files will be sorted into subdirectories in the destination according to the `collection` attribute in the document metadata.

You may have to set the `PYTHONPATH` environment variable for correct path resolution, e.g. :
```sh
export PYTHONPATH="$PYTHONPATH:wordprofile"
```

#### Examples

Converts `filename.tabs` to conllu and prints on console.
```shell script
$ python tabs2conllu.py -i some/path/filename.tabs
```

Converts `filename.tabs` to conllu and writes to destination path with separate collection subdirs.
```shell script
$ python tabs2conllu.py -i some/path/filename.tabs --output some/target/path
```

Converts all files matching the pattern (glob) to conllu, saves everything to subfolders in target path.
Please note using quotation for patterns.
```shell script
$ tabs2conllu -i "some/**/*.tabs" --output here/is/the/corpus
```

## Setup and Testing

### Installation
see [readme](../README.md) for `wordprofile`.

Tests:

- Run Unit Tests: `pytest -v`

# II Annotation of Dependency Relations
For the annotation of  dependeny relations, a model should be used that was trained on [HDT tag set](https://nats-www.informatik.uni-hamburg.de/HDT/), e.g. [`de_dwds_dep_hdt_dist`](https://huggingface.co/zentrum-lexikographie/de_dwds_dep_hdt_dist) for  parsing with [`spacy`](https://spacy.io/).

If the environment has gpu/cuda enabled, use the `de_dwds_dep_hdt_dist`, otherwise the [`de_dwds_dep_hdt_lg`](https://huggingface.co/zentrum-lexikographie/de_dwds_dep_hdt_lg) can be used on cpu.

To download a model, run for example:

    pip install https://huggingface.co/zentrum-lexikographie/de_dwds_dep_hdt_lg/resolve/main/de_dwds_dep_hdt_lg-any-py3-none-any.whl

For the annotation, the script `annotate_deprel.py` can be used:
```sh
Usage: annotate_deprel.py [OPTIONS]

  Parse conll file and add dependency relation annotations.

Options:
  -i, --input FILENAME      Path to input file in conllu format.
  -o, --output FILENAME     Output file.
  -m, --model TEXT          Name of spacy model, default is
                            'de_dwds_dep_hdt_dist'.
  -b, --batch-size INTEGER  Batch size used by model during processing.
                            Default is 128 (sentences).
  --help                    Show this message and exit.
```
