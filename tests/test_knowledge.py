from shellforgeai.knowledge.search import search_local


def test_local_search(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello nginx")
    r = search_local([str(tmp_path)], "nginx")
    assert r
