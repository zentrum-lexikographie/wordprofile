# Preprocessing
Convert ZDL-internal DDC-Dump/Tabs files to conllu format.

(Adaption of [`pytabs`](https://git.zdl.org/zdl/pytabs) project by René Knaebel.)

## Usage
```shell script
Usage: tabs2conllu [OPTIONS]

  Tabs to Conllu conversion

Options:
  -i, --input TEXT                Glob compatible path pattern for source
                                  files.
  -o, --output TEXT               Path to destination folder.
  -x, --remove-xml                Removes invalid xml fragments from tokens.
  -v, --remove-invalid-sentences  Removes sentences that do not fit hard
                                  constraints.
  -h, --help                      Show this message and exit.

```

The option `--remove-invalid-sentences` filters sentences that contain at least four valid tokens. Tokens are valid if they are not POS-tagged as punctuation or as unknown (e.g. foreign-language or truncated tokens and abbreviations).

## Examples

Converts `filename.tabs` to conllu and prints on console.
```shell script
$ tabs2conllu -i some/path/filename.tabs
```

Converts `filename.tabs` to conllu and writes to destination path with separate collection subdirs.
```shell script
$ tabs2conllu -i some/path/filename.tabs --output some/target/path
```

Converts all files matching the pattern (glob) to conllu, normalizes, saves everything to subfolders in target path.
Please note using quotation for patterns.
```shell script
$ tabs2conllu -i "some/**/*.tabs" --output here/is/the/corpus --remove-xml --remove-invalid-sentences
```

## Setup and Testing

### Installation
see [readme](../README.md) for `wordprofile`.

Tests:

- Run Unit Tests: `pytest -v`
