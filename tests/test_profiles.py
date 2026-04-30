from pathlib import Path

from shellforgeai.core.profiles import load_profile


def test_profile_loads_inspect():
    assert load_profile("inspect", Path.cwd()).name == "inspect"
