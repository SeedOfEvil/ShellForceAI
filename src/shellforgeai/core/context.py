from __future__ import annotations

from pydantic import BaseModel

from shellforgeai.core.config import Settings
from shellforgeai.core.profiles import Profile
from shellforgeai.core.session import SessionContext


class RuntimeContext(BaseModel):
    settings: Settings
    profile: Profile
    session: SessionContext
    verbose: bool = False
