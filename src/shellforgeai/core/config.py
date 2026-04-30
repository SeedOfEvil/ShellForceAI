import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class AppCfg(BaseModel):
    name: str
    data_dir: Path
    default_profile: str


class ModelCfg(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key_env: str
    timeout_seconds: int


class KnowledgeCfg(BaseModel):
    local_paths: list[str]
    online_enabled: bool


class AuditCfg(BaseModel):
    enabled: bool
    jsonl: str
    artifact_output: str


class PolicyCfg(BaseModel):
    default_action: str
    deny_danger_without_breakglass: bool


class Settings(BaseModel):
    app: AppCfg
    model: ModelCfg
    knowledge: KnowledgeCfg
    audit: AuditCfg
    policy: PolicyCfg


def load_settings(config_path: Path | None = None) -> Settings:
    base = Path(__file__).resolve().parents[3] / "config/default.yaml"
    data = yaml.safe_load(base.read_text())
    if config_path and config_path.exists():
        data.update(yaml.safe_load(config_path.read_text()))
    data["app"]["data_dir"] = os.getenv("SHELLFORGEAI_DATA_DIR", data["app"]["data_dir"])
    return Settings.model_validate(data)
