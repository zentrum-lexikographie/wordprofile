import os
import tempfile

import wordprofile.preprocessing.cli.data_update as du


def test_current_basename_discovery():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "corpus.toc"), "w") as toc_file:
            toc_file.write("first/basename\nsecond/basename\n")
        result = du.collect_current_basenames(tmpdir, "corpus")
    assert result == {"first/basename", "second/basename"}


def test_current_basename_discovery_with_nested_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "corpus.toc"), "w") as toc_file:
            toc_file.write("first/basename1\nfirst/basename2\n")
        sub1 = tempfile.mkdtemp(dir=tmpdir)
        with open(os.path.join(sub1, "corpus.toc"), "w") as toc_file:
            toc_file.write("second/basename3\nsecond/basename4\n")
        sub2 = tempfile.mkdtemp(dir=sub1)
        with open(os.path.join(sub2, "corpus.toc"), "w") as toc_file:
            toc_file.write("third/basename5\n")
        result = du.collect_current_basenames(tmpdir, "corpus")
    assert result == {
        "first/basename1",
        "first/basename2",
        "second/basename3",
        "second/basename4",
        "third/basename5",
    }


def test_basename_to_tabs_mapping():
    with tempfile.TemporaryDirectory() as tmpdir:
        tabs_file = os.path.join(tmpdir, "corpus-tabs.files")
        with open(tabs_file, "w") as fp:
            fp.write(
                "corpus-tabs.d/1996/01/19960101.tabs\n"
                "corpus-tabs.d/1996/04/19960416.tabs\n"
                "corpus-tabs.d/1996/04/19960417.tabs"
            )
        result = du.map_tabs_file_to_basename(tabs_file)
    assert result == {
        "corpus-tabs.d/1996/01/19960101.tabs": "1996/01/19960101",
        "corpus-tabs.d/1996/04/19960416.tabs": "1996/04/19960416",
        "corpus-tabs.d/1996/04/19960417.tabs": "1996/04/19960417",
    }


def test_filte_new_files():
    old_basenames = {"ab", "cd", "e/f"}
    new_files = {
        "corpus-tabs.d/ab.tabs": "ab",
        "corpus-tabs.d/a/b.tabs": "a/b",
        "corpus-tabs.d/g/asb.tabs": "g/asb",
        "corpus-tabs.d/e/f.tabs": "e/f",
    }
    result = du.filter_new_files(old_basenames, new_files)
    assert result == ["corpus-tabs.d/a/b.tabs", "corpus-tabs.d/g/asb.tabs"]
