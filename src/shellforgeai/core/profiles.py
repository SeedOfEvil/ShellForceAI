from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from shellforgeai.policy.risk import RiskTier


class Profile(BaseModel):
    name: str
    description: str = ""
    allow_risks: list[RiskTier] = Field(default_factory=list)
    ask_risks: list[RiskTier] = Field(default_factory=list)
    deny_risks: list[RiskTier] = Field(default_factory=list)
    allow_shell_raw: bool = False
    online_allowed: bool = False


def load_profile(name: str, repo_root: Path) -> Profile:
    return Profile.model_validate(
        yaml.safe_load((repo_root / "config/profiles" / f"{name}.yaml").read_text())
    )
