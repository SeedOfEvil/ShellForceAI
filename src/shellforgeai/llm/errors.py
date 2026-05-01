from __future__ import annotations


class ModelError(Exception):
    """Base model provider error."""


class ProviderUnavailableError(ModelError):
    pass


class ModelTimeoutError(ModelError):
    pass
