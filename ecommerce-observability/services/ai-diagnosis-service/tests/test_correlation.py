from app.schemas.incident import Incident, IncidentContext
from app.services.correlation import correlate_evidence


def test_correlate_service_unavailable():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceOrderServiceMissing",
                service="order-service",
                severity="critical",
                summary="Order Service target is missing",
            )
        ],
        prometheus={
            "service": "order-service",
            "up": [
                {
                    "metric": {
                        "service": "order-service",
                    },
                    "value": [1234567890, "0"],
                }
            ]
        },
        kubernetes={
            "service": "order-service",
            "deployment": {
                "name": "order-service",
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            "pods": [],
        },
        loki={
            "service": "order-service",
            "logs": [],
            "error_logs": [],
        }
    )

    result = correlate_evidence(context)

    assert result.consistent is True
    assert "Prometheus target is down" in result.signals
    assert (
        "Kubernetes deployment has no ready replicas"
        in result.signals
    )
    assert len(result.root_cause_candidates) == 1

    candidate = result.root_cause_candidates[0]

    assert candidate.cause == "order-service is unavailable"
    assert "Prometheus target is down" in candidate.evidence
    assert (
        "Kubernetes deployment has no ready replicas"
        in candidate.evidence
    )
    assert candidate.confidence == 0.95