from shellforgeai.core.config import load_settings


def test_config_loads_default() -> None:
    assert load_settings().app.name == "ShellForgeAI"
