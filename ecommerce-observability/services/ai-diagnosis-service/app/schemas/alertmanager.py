from typing import Any

from pydantic import BaseModel, Field


class Alert(BaseModel):
    status: str
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None
    endsAt: str | None = None
    generatorURL: str | None = None


class AlertmanagerWebhook(BaseModel):
    version: str | None = None
    groupKey: str | None = None
    truncatedAlerts: int = 0
    status: str
    receiver: str
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = None
    alerts: list[Alert] = Field(default_factory=list)

    model_config = {
        "extra": "allow"
    }