from app.schemas.diagnosis_result import DiagnosisResult


def test_diagnosis_result():
    result = DiagnosisResult(
        root_cause="order-service is unavailable",
        explanation=(
            "The Order Service is unavailable because "
            "its Kubernetes deployment has no ready replicas."
        ),
        affected_service="order-service",
        evidence=[
            "Prometheus target is down",
            "Kubernetes deployment has no ready replicas",
        ],
        confidence=0.95,
        impact="Order creation is unavailable.",
        recommendations=[
            "Check the Order Service deployment and pod status.",
            "Inspect recent Kubernetes warning events.",
        ],
    )

    assert result.root_cause == "order-service is unavailable"
    assert result.affected_service == "order-service"
    assert result.confidence == 0.95
    assert len(result.evidence) == 2
    assert len(result.recommendations) == 2