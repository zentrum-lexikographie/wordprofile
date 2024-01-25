from conllu.models import Metadata

import wordprofile.wpse.prepare as pre
from wordprofile.wpse.db_tables import DBCorpusFile


def test_prepare_corpus_file():
    metadata = Metadata(
        {
            "DDC:meta.file_": "path/to/file",
            "text": "text",
            "DDC:meta.collection": "coll",
            "DDC:meta.basename": "basename",
            "DDC:meta.bibl": "bibl",
            "DDC:meta.biblLext": "biblLex",
            "DDC:meta.data_": "data",
            "DDC:meta.textClass": "textclass",
        }
    )
    result = pre.prepare_corpus_file(metadata)
    assert result[0] == "path/to/file"
    assert isinstance(result[1], DBCorpusFile)
    assert result[1].id == result[0]
    assert result[1].corpus == "coll"
    assert result[1].orig == "bibl"


def test_prepare_concord_sentence():
    pass


def test_prepare_matches():
    pass
