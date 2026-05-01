from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModelRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    messages: list[dict[str, str]] | None = None
    model: str
    provider: str
    temperature: float | None = None
    max_output_tokens: int | None = None
    timeout_seconds: int = 180
    json_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    provider: str
    model: str
    text: str
    structured: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    ok: bool = True
    error: str | None = None
    duration_ms: int = 0
    usage: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)


class LikelyCause(BaseModel):
    title: str
    explanation: str
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class RecommendedStep(BaseModel):
    title: str
    description: str
    risk: str = "low"
    requires_approval: bool = True
    command: str | None = None
    destructive: bool = False


class ModelDiagnosis(BaseModel):
    summary: str
    likely_causes: list[LikelyCause] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_next_steps: list[RecommendedStep] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    unknowns: list[str] = Field(default_factory=list)
