from app.schemas.correlation import CorrelationResult
from app.schemas.diagnosis import DiagnosisState
from app.schemas.evidence import (
    DependencyEvidence,
    InfrastructureEvidence,
    OSEvidence,
    ServiceEvidence,
)
from app.schemas.incident import Incident


def test_diagnosis_state():
    incident = Incident(
        status="firing",
        alertname="EcommerceOrderServiceMissing",
        service="order-service",
        severity="critical",
        summary="Order Service target is missing",
    )

    state = DiagnosisState(
        incident=incident,

        service_evidence=ServiceEvidence(
            metrics={
                "up": [{
                        "value": [1234567890,"0",]
                    }]
            },
            logs={
                "logs": [],
                "error_logs": [],
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
            }
        ),

        infrastructure_evidence=InfrastructureEvidence(
            pods=[{
                    "name": "order-service-123",
                    "phase": "Running",
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
            ]
        ),

        os_evidence=OSEvidence(
            cpu={
                "usage_percent": 25.0,
            },
            memory={
                "available_bytes": 1024,
            }
        ),

        correlation=CorrelationResult(
            consistent=True,
            signals=[
                "Prometheus target is down",
                "Kubernetes deployment has no ready replicas",
            ],
            root_cause_candidates=[
                "order-service is unavailable",
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