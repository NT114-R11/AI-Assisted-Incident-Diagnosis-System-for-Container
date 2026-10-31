from app.graph.workflow import diagnosis_graph
from app.schemas.diagnosis import DiagnosisState
from app.schemas.evidence import (ServiceEvidence, DependencyEvidence, InfrastructureEvidence, OSEvidence)
from app.schemas.incident import Incident


def test_diagnosis_graph():
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
                "up": [{"value": [1234567890,"0",]}]
            },
            logs={
                "logs": [],
                "error_logs": [],
            },
        )
    )

    result = diagnosis_graph.invoke(state)

    assert result["incident"].service == "order-service"

    assert result["incident"].alertname == ("EcommerceOrderServiceMissing")

    assert ("Service target is down"in result["correlation"].signals)

def test_diagnosis_graph_healthy_dependencies():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={"up": [{"value": [1234567890,"0"]}]
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
            }))

    result = diagnosis_graph.invoke(state)

    signals = result["correlation"].signals

    assert "Dependency cart-service is healthy" in signals
    assert "Dependency user-service is healthy" in signals
    assert "PostgreSQL dependency is healthy" in signals


def test_diagnosis_graph_failed_dependency():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={"up": [{"value": [1234567890,"0"]}]}
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
            }))

    result = diagnosis_graph.invoke(state)

    signals = result["correlation"].signals

    assert ("Dependency cart-service is unreachable" in signals)
    assert "Dependency user-service is healthy" in signals
    assert "PostgreSQL dependency is healthy" in signals

def test_diagnosis_graph_infrastructure():
    state = DiagnosisState(
        incident=Incident(
            status="firing",
            alertname="EcommerceOrderServiceMissing",
            service="order-service",
            severity="critical",
        ),
        service_evidence=ServiceEvidence(
            metrics={"up": [{"value": [1234567890,"0"]}]}
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
                    ]}],
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
            ]))

    result = diagnosis_graph.invoke(state)

    signals = result["correlation"].signals

    assert ("Kubernetes deployment has no ready replicas"in signals)

    assert (
        "Kubernetes deployment has insufficient "
        "ready replicas: 0/1"
        in signals)

    assert (
        "Container order-service in pod order-service-123 "
        "is not ready"
        in signals)

    assert (
        "Container order-service in pod order-service-123 "
        "has restarted 3 time(s)"
        in signals)

    assert (
        "Kubernetes warning event: Unhealthy"
        in signals)

def test_diagnosis_graph_os():
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
        )
    )

    result = diagnosis_graph.invoke(state)
    signals = result["correlation"].signals

    assert ("OS CPU usage is critical: 95.0%" in signals)
    assert ("OS memory usage is critical: 92.0%" in signals)
    assert ("OS disk usage is elevated: 85.0%" in signals)
    assert ("OS network errors detected: 5" in signals)
