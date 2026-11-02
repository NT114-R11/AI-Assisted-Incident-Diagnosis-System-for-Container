from app.schemas.correlation import CorrelationResult, RootCauseCandidate
from app.schemas.diagnosis import DiagnosisState
from app.schemas.evidence import (
    DependencyEvidence,
    InfrastructureEvidence,
    OSEvidence,
    ServiceEvidence,
)
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.incident import Incident
from app.graph.nodes import generate_diagnosis
import pytest

def test_diagnosis_state():
    incident = Incident(
        status="firing",
        alertname="EcommerceOrderServiceMissing",
        service="order-service",
        severity="critical",
        summary="Order Service target is missing")

    state = DiagnosisState(
        incident=incident,

        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890,"0",]}]},
            logs={
                "logs": [],
                "error_logs": []}),

        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": True,
                    "status_code": 200
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200
                }
            ],
            postgres={
                "service": "postgres",
                "healthy": True}),

        infrastructure_evidence=InfrastructureEvidence(
            pods=[{
                    "name": "order-service-123",
                    "phase": "Running"
                }],
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0
            },
            events=[
                {
                    "type": "Warning",
                    "reason": "Unhealthy",
                }]),
        os_evidence=OSEvidence(
            cpu={"usage_percent": 25.0,},
            memory={"available_bytes": 1024,}),

        correlation=CorrelationResult(
            consistent=True,
            signals=[
                "Prometheus target is down",
                "Kubernetes deployment has no ready replicas",
            ],

            root_cause_candidates=[
                RootCauseCandidate(
                    cause="order-service is unavailable",
                    evidence=[
                        "Prometheus target is down",
                        "Kubernetes deployment has no ready replicas",
                    ],
                    confidence=0.95,
                ),
            ]))

    assert state.incident.service == "order-service"
    assert (state.service_evidence.metrics["up"][0]["value"][-1]== "0")
    assert (state.dependency_evidence.services[0]["service"]== "cart-service")
    assert (state.dependency_evidence.postgres["healthy"] is True)
    assert (state.infrastructure_evidence.deployments["ready_replicas"]== 0)
    assert (state.infrastructure_evidence.events[0]["reason"]== "Unhealthy")
    assert (state.os_evidence.cpu["usage_percent"]== 25.0)
    assert state.correlation.consistent is True
    assert state.diagnosis is None
    assert state.confidence is None
    assert state.recommendations == []

@pytest.mark.asyncio
async def test_generate_diagnosis_result():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
            summary="Order Service is unavailable",
        ),
        correlation=CorrelationResult(
            consistent=True,
            signals=[
                "Service target is down",
                "Kubernetes deployment has no ready replicas",
            ],
            root_cause_candidates=[
                RootCauseCandidate(
                    cause="order-service is unavailable",
                    evidence=[
                        "Service target is down",
                        "Kubernetes deployment has no ready replicas",
                    ],
                    confidence=0.95,
                    score=0.92,
                )
            ],
        ),
    )

    fake_llm = MagicMock()
    fake_llm.diagnose = AsyncMock(
        return_value=(
            "The order-service is unavailable because its "
            "Kubernetes deployment has no ready replicas."
        )
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=fake_llm,
    ):
        result = await generate_diagnosis(state)

    assert result.diagnosis_result is not None

    assert (
        result.diagnosis_result.root_cause
        == "order-service is unavailable"
    )

    assert (
        result.diagnosis_result.affected_service
        == "order-service"
    )

    assert result.diagnosis_result.confidence == 0.92

    assert (
        result.diagnosis_result.explanation
        == (
            "The order-service is unavailable because its "
            "Kubernetes deployment has no ready replicas."
        )
    )

    assert (
        "Service target is down"
        in result.diagnosis_result.evidence
    )

    assert (
        "Kubernetes deployment has no ready replicas"
        in result.diagnosis_result.evidence
    )

    assert len(result.diagnosis_result.recommendations) == 3

    fake_llm.diagnose.assert_awaited_once()


