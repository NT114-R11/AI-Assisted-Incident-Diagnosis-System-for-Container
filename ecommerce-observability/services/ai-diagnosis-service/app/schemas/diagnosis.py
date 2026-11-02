from typing import Any

from pydantic import BaseModel, Field
from app.schemas.diagnosis_result import DiagnosisResult
from app.schemas.correlation import CorrelationResult
from app.schemas.evidence import (
    DependencyEvidence,
    InfrastructureEvidence,
    OSEvidence,
    ServiceEvidence)
from app.schemas.incident import Incident


class DiagnosisState(BaseModel):
    incident: Incident | None = None

    service_evidence: ServiceEvidence = Field(default_factory=ServiceEvidence)

    dependency_evidence: DependencyEvidence = Field(default_factory=DependencyEvidence)

    infrastructure_evidence: InfrastructureEvidence = Field(default_factory=InfrastructureEvidence)

    os_evidence: OSEvidence = Field(default_factory=OSEvidence)

    correlation: CorrelationResult | None = None

    diagnosis: str | None = None
    confidence: float | None = None
    recommendations: list[str] = Field(default_factory=list)
    diagnosis_result: DiagnosisResult | None = None