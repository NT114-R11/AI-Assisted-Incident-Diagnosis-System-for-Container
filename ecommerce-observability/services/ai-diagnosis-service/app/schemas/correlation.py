from pydantic import BaseModel, Field


class CorrelationResult(BaseModel):
    consistent: bool = False
    signals: list[str] = Field(default_factory=list)
    root_cause_candidates: list[str] = Field(default_factory=list)