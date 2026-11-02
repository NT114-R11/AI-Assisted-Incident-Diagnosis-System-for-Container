from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.graph.nodes import generate_diagnosis
from app.graph.workflow import diagnosis_graph
from app.schemas.correlation import CorrelationResult, RootCauseCandidate
from app.schemas.diagnosis import DiagnosisState
from app.schemas.evidence import (
    DependencyEvidence,
    InfrastructureEvidence,
    OSEvidence,
    ServiceEvidence,
)
from app.schemas.incident import Incident


def mock_llm():
    fake_response = MagicMock()
    fake_response.output_text = (
        "The incident is explained by the deterministic root cause "
        "identified from the available evidence."
    )

    mock_client = MagicMock()
    mock_client.diagnose = AsyncMock(
        return_value=fake_response.output_text
    )

    return mock_client


@pytest.mark.asyncio
async def test_diagnosis_graph():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
            summary="Order Service target is missing",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            },
            logs={
                "logs": [],
                "error_logs": [],
            },
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    assert result["incident"].service == "order-service"
    assert result["incident"].alertname == "EcommerceOrderServiceMissing"
    assert "Service target is down" in result["correlation"].signals


@pytest.mark.asyncio
async def test_diagnosis_graph_healthy_dependencies():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            }
        ),
        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": True,
                    "status_code": 200,
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200,
                },
            ],
            postgres={
                "service": "postgres",
                "healthy": True,
            },
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    signals = result["correlation"].signals

    assert "Dependency cart-service is healthy" in signals
    assert "Dependency user-service is healthy" in signals
    assert "PostgreSQL dependency is healthy" in signals


@pytest.mark.asyncio
async def test_diagnosis_graph_failed_dependency():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            }
        ),
        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": False,
                    "status_code": None,
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200,
                },
            ],
            postgres={
                "service": "postgres",
                "healthy": True,
            },
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    signals = result["correlation"].signals

    assert "Dependency cart-service is unreachable" in signals
    assert "Dependency user-service is healthy" in signals
    assert "PostgreSQL dependency is healthy" in signals


@pytest.mark.asyncio
async def test_diagnosis_graph_infrastructure():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            }
        ),
        infrastructure_evidence=InfrastructureEvidence(
            pods=[
                {
                    "name": "order-service-123",
                    "phase": "Running",
                    "containers": [
                        {
                            "name": "order-service",
                            "ready": False,
                            "restart_count": 3,
                        }
                    ],
                }
            ],
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            events=[
                {
                    "type": "Warning",
                    "reason": "Unhealthy",
                }
            ],
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    signals = result["correlation"].signals

    assert "Kubernetes deployment has no ready replicas" in signals

    assert (
        "Container order-service in pod order-service-123 "
        "is not ready"
        in signals
    )

    assert (
        "Container order-service in pod order-service-123 "
        "has restarted 3 time(s)"
        in signals
    )

    assert "Kubernetes warning event: Unhealthy" in signals


@pytest.mark.asyncio
async def test_diagnosis_graph_os():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        os_evidence=OSEvidence(
            cpu={"usage_percent": 95.0},
            memory={"usage_percent": 92.0},
            disk={"usage_percent": 85.0},
            network={"errors": 5},
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    signals = result["correlation"].signals

    assert "OS CPU usage is critical: 95.0%" in signals
    assert "OS memory usage is critical: 92.0%" in signals
    assert "OS disk usage is elevated: 85.0%" in signals
    assert "OS network errors detected: 5" in signals


@pytest.mark.asyncio
async def test_diagnosis_graph_correlates_service_failure():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            }
        ),
        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": True,
                    "status_code": 200,
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200,
                },
            ],
            postgres={
                "service": "postgres",
                "healthy": True,
            },
        ),
        infrastructure_evidence=InfrastructureEvidence(
            pods=[],
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            events=[],
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    correlation = result["correlation"]

    assert correlation.consistent is True
    assert len(correlation.root_cause_candidates) >= 1

    candidate = correlation.root_cause_candidates[0]

    assert candidate.cause == "order-service is unavailable"
    assert "Service target is down" in candidate.evidence
    assert "Kubernetes deployment has no ready replicas" in candidate.evidence
    assert candidate.confidence == 0.95


@pytest.mark.asyncio
async def test_diagnosis_graph_correlates_dependency_failure():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": False,
                    "status_code": None,
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200,
                },
            ],
            postgres={
                "service": "postgres",
                "healthy": True,
            },
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    correlation = result["correlation"]

    assert correlation.consistent is True

    dependency_candidates = [
        candidate
        for candidate in correlation.root_cause_candidates
        if "cart-service" in candidate.cause
    ]

    assert len(dependency_candidates) == 1

    candidate = dependency_candidates[0]

    assert candidate.cause == "cart-service is unavailable or unhealthy"
    assert candidate.confidence == 0.85
    assert candidate.evidence == [
        "Dependency cart-service is unreachable"
    ]


@pytest.mark.asyncio
async def test_diagnosis_graph_ranks_competing_root_causes():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "0"]}]
            }
        ),
        dependency_evidence=DependencyEvidence(
            services=[
                {
                    "service": "cart-service",
                    "healthy": False,
                    "status_code": None,
                },
                {
                    "service": "user-service",
                    "healthy": True,
                    "status_code": 200,
                },
            ],
            postgres={
                "service": "postgres",
                "healthy": True,
            },
        ),
        infrastructure_evidence=InfrastructureEvidence(
            pods=[
                {
                    "name": "order-service-123",
                    "phase": "Running",
                    "containers": [
                        {
                            "name": "order-service",
                            "ready": False,
                            "restart_count": 3,
                        }
                    ],
                }
            ],
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            events=[
                {
                    "type": "Warning",
                    "reason": "Unhealthy",
                }
            ],
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    candidates = result["correlation"].root_cause_candidates

    assert len(candidates) >= 2
    assert candidates[0].cause == "order-service is unavailable"
    assert candidates[0].score > candidates[1].score
    assert candidates[0].confidence == 0.95


@pytest.mark.asyncio
async def test_diagnosis_graph_generates_diagnosis_result():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
            summary="Order Service is unavailable",
        ),
        service_evidence={
            "metrics": {
                "up": [
                    {
                        "metric": {"service": "order-service"},
                        "value": ["0", "0"],
                    }
                ]
            },
            "logs": {},
        },
        infrastructure_evidence={
            "deployments": {
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            "pods": [],
            "events": [],
        },
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    diagnosis = result["diagnosis_result"]

    assert diagnosis is not None
    assert diagnosis.root_cause == "order-service is unavailable"
    assert diagnosis.affected_service == "order-service"
    assert diagnosis.confidence > 0.0

    assert "Service target is down" in diagnosis.evidence
    assert "Kubernetes deployment has no ready replicas" in diagnosis.evidence
    assert len(diagnosis.recommendations) == 3

    assert (diagnosis.explanation
        == "The incident is explained by the deterministic root cause "
        "identified from the available evidence.")

@pytest.mark.asyncio
async def test_generate_diagnosis_falls_back_when_llm_fails():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
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
    fake_llm.diagnose = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

    with patch("app.graph.nodes.LLMClient",return_value=fake_llm):
        result = await generate_diagnosis(state)

    diagnosis = result.diagnosis_result

    assert diagnosis is not None
    assert diagnosis.root_cause == "order-service is unavailable"
    assert diagnosis.affected_service == "order-service"
    assert diagnosis.confidence == 0.92

    assert (
        diagnosis.explanation== (
            "order-service is unavailable. "
            "The diagnosis is supported by "
            "2 piece(s) of evidence."
        ))

    assert "Service target is down" in diagnosis.evidence
    assert (
        "Kubernetes deployment has no ready replicas"
        in diagnosis.evidence)

    fake_llm.diagnose.assert_awaited_once()

@pytest.mark.asyncio
async def test_diagnosis_graph_high_error_rate():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceHighErrorRate",
            service="order-service",
            severity="warning",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "1"]}],
                "error_rate": 0.18,
            },
            logs={
                "error_logs": [],
            },
        ),
        infrastructure_evidence=InfrastructureEvidence(
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 1,
                "available_replicas": 1,
            }
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    candidates = result["correlation"].root_cause_candidates
    assert candidates[0].cause == (
        "order-service has an elevated HTTP error rate"
    )
    assert "Service error rate is elevated: 0.18" in candidates[0].evidence


@pytest.mark.asyncio
async def test_diagnosis_graph_high_latency():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceHighLatency",
            service="cart-service",
            severity="warning",
        ),
        service_evidence=ServiceEvidence(
            metrics={
                "up": [{"value": [1234567890, "1"]}],
                "p95_latency": 3.4,
            }
        ),
        infrastructure_evidence=InfrastructureEvidence(
            deployments={
                "desired_replicas": 1,
                "ready_replicas": 1,
                "available_replicas": 1,
            }
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    candidates = result["correlation"].root_cause_candidates
    assert candidates[0].cause == (
        "cart-service has elevated request latency"
    )
    assert "Service p95 latency is elevated: 3.4s" in candidates[0].evidence


@pytest.mark.asyncio
async def test_diagnosis_graph_unknown_signal_uses_generic_candidate():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="FutureIncidentType",
            service="product-service",
            severity="warning",
        ),
        correlation=CorrelationResult(
            signals=["New observability signal detected"],
        ),
    )

    with patch(
        "app.graph.nodes.LLMClient",
        return_value=mock_llm(),
    ):
        result = await diagnosis_graph.ainvoke(state)

    candidates = result["correlation"].root_cause_candidates
    assert len(candidates) == 1
    assert candidates[0].confidence == 0.40
    assert "New observability signal detected" in candidates[0].evidence
