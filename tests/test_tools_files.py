from shellforgeai.tools.files import read, stat


def test_files_read_missing():
    assert not read("/nope").ok


def test_files_stat_missing():
    assert "False" in stat("/nope").stdout
