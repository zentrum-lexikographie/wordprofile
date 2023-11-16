from pathlib import Path

from preprocessing.pytabs.tabs import TabsDocument

test_dir = (Path(__file__) / "..").resolve()
sample_tabs_file = test_dir / "testdata" / "sample.tabs"
sample_conllu_file = test_dir / "testdata" / "sample.conllu"


def test_tabs2conllu():
    expected = sample_conllu_file.read_text()
    doc = TabsDocument.from_tabs(sample_tabs_file.as_posix())
    assert expected == doc.as_conllu()
