from shellforgeai.tools.host import host_info


def test_host_info():
    assert "hostname" in host_info().stdout
