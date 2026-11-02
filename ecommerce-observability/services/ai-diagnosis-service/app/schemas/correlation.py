from pydantic import BaseModel, Field


class RootCauseCandidate(BaseModel):
    cause: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0 # confidence level of a rule when generating a candidate
    score: float = 0.0 # candidate priority level relative to other candidates


class CorrelationResult(BaseModel):
    consistent: bool = False
    signals: list[str] = Field(default_factory=list)
    root_cause_candidates: list[RootCauseCandidate] = Field(default_factory=list)