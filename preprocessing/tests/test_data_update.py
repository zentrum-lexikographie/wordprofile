import os
import tempfile

import preprocessing.pytabs.cli.data_update as du


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
