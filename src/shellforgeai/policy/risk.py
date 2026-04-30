from enum import Enum


class RiskTier(str, Enum):
    read = "read"
    change = "change"
    service = "service"
    system = "system"
    danger = "danger"


class PolicyAction(str, Enum):
    allow = "allow"
    ask = "ask"
    deny = "deny"
