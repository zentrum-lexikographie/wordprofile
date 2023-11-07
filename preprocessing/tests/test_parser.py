from pathlib import Path

from pytabs.parser import parse, add_space_after

test_dir = (Path(__file__) / '..').resolve()
sample_tabs_file = test_dir / 'sample.tabs'

token_fields = ['Token', 'Pos', 'Lemma', 'WordSep', 'SpaceAfter']


def test_parse():
    with sample_tabs_file.open() as f:
        sentences = list(add_space_after(parse(f)))
        assert len(sentences) > 0
        for sentence in sentences:
            assert sentence['token_fields'] == token_fields
            for token in sentence['tokens']:
                assert len(token) == len(token_fields)
