from typing import Any

from pydantic import BaseModel, Field

from app.schemas.correlation import CorrelationResult


class Incident(BaseModel):
    status: str
    alertname: str | None = None
    service: str | None = None
    severity: str | None = None
    summary: str | None = None
    description: str | None = None
    starts_at: str | None = None


class IncidentContext(BaseModel):
    status: str
    receiver: str
    incident_count: int = 0
    incidents: list[Incident] = Field(default_factory=list)

    prometheus: Any | None = None
    loki: Any | None = None
    kubernetes: Any | None = None

    correlation: CorrelationResult | None = None

    diagnosis: str | None = None