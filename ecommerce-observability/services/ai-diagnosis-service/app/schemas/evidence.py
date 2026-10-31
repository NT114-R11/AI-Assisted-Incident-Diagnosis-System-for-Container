from typing import Any

from pydantic import BaseModel, Field


class ServiceEvidence(BaseModel):
    metrics: dict[str, Any] = Field(default_factory=dict)
    logs: dict[str, Any] = Field(default_factory=dict)


class DependencyEvidence(BaseModel):
    services: list[dict[str, Any]] = Field(default_factory=list)
    postgres: dict[str, Any] = Field(default_factory=dict)


class InfrastructureEvidence(BaseModel):
    pods: list[dict[str, Any]] = Field(default_factory=list)
    deployments: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)


class OSEvidence(BaseModel):
    cpu: dict[str, Any] = Field(default_factory=dict)
    memory: dict[str, Any] = Field(default_factory=dict)
    disk: dict[str, Any] = Field(default_factory=dict)
    network: dict[str, Any] = Field(default_factory=dict)