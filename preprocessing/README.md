# Preprocessing
Convert ZDL-internal DDC-Dump/Tabs files to conllu format.

(This is a copy of [`pytabs`](https://git.zdl.org/zdl/pytabs) project by René Knaebel.)

## Usage
```shell script
usage: tabs2conllu [-h] [--destination DESTINATION] [--remove-xml]
                   [--remove-invalid-sentences]
                   source

Tabs to Conllu Conversion

positional arguments:
  source                Glob compatible path pattern for source files.

optional arguments:
  -h, --help            show this help message and exit
  --destination DESTINATION
                        Path to destination folder.
  --remove-xml          Removes invalid xml from tokens.
  --remove-invalid-sentences
                        Removes sentences that do not fit hard constraints
```

## Examples

Converts `filename.tabs` to conllu and prints on console.
```shell script
$ tabs2conllu some/path/filename.tabs
```

Converts `filename.tabs` to conllu and writes to destination path with separate collection subdirs.
```shell script
$ tabs2conllu some/path/filename.tabs --destination some/target/path
```

Converts all files matching the pattern (glob) to conllu, normalizes, saves everything to subfolders in target path.
Please note using quotation for patterns.
```shell script
$ tabs2conllu "some/**/*.tabs" --destination here/is/the/corpus --remove-xml remove-invalid-sentences
```

## Other Commands

### Installation
see [readme](../README.md) for `wordprofile`.

Tests:

- Run Unit Tests: `pytest -v`
