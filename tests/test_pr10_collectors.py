from shellforgeai.tools import files, logs, system


def test_files_read_text_denies_sensitive():
    r = files.read_text("/etc/shadow")
    assert not r.ok


def test_logs_find_common_nginx():
    r = logs.find_common("nginx")
    assert r.tool == "logs.find_common"


def test_system_container_detect_runs():
    r = system.container_detect()
    assert r.tool == "system.container_detect"
