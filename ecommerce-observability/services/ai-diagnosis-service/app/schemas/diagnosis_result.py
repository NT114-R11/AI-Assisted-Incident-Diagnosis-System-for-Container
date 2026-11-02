from pydantic import BaseModel, Field


class DiagnosisResult(BaseModel):
    root_cause: str
    explanation: str
    affected_service: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    impact: str
    recommendations: list[str] = Field(default_factory=list)