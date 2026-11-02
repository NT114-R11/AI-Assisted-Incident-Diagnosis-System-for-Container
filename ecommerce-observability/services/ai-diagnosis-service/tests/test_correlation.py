
from app.schemas.incident import Incident, IncidentContext
from app.services.correlation import correlate_evidence, rank_root_causes



def test_correlate_high_error_rate():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceHighErrorRate",
                service="order-service",
                severity="warning",
            )
        ],
        prometheus={
            "error_rate": 0.18,
        },
        kubernetes={
            "deployment": {
                "desired_replicas": 1,
                "ready_replicas": 1,
            }
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True
    assert result.root_cause_candidates[0].cause == (
        "order-service has an elevated HTTP error rate"
    )


def test_correlate_high_latency():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceHighLatency",
                service="cart-service",
                severity="warning",
            )
        ],
        prometheus={
            "p95_latency": 3.4,
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True
    assert result.root_cause_candidates[0].cause == (
        "cart-service has elevated request latency"
    )

def test_correlate_crashloopbackoff():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceServiceDown",
                service="order-service",
                severity="critical",
            )
        ],
        kubernetes={
            "pods": [
                {
                    "name": "order-service-abc123",
                    "phase": "Running",
                    "containers": [
                        {
                            "name": "order-service",
                            "ready": False,
                            "restart_count": 8,
                            "state": "waiting",
                            "reason": "CrashLoopBackOff",
                            "message": "Back-off restarting failed container",
                            "last_state": "terminated",
                            "last_reason": "Error",
                        }
                    ],
                }
            ]
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True

    candidates = [
        candidate
        for candidate in result.root_cause_candidates
        if "container restart failure" in candidate.cause
    ]

    assert candidates
    assert any(
        "CrashLoopBackOff" in evidence
        for evidence in candidates[0].evidence
    )

def test_correlate_image_pull_failure():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceServiceDown",
                service="product-service",
                severity="critical",
            )
        ],
        kubernetes={
            "pods": [
                {
                    "name": "product-service-abc123",
                    "phase": "Pending",
                    "containers": [
                        {
                            "name": "product-service",
                            "ready": False,
                            "restart_count": 0,
                            "state": "waiting",
                            "reason": "ImagePullBackOff",
                            "message": "Back-off pulling image",
                            "last_state": None,
                            "last_reason": None,
                        }
                    ],
                }
            ]
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True

    candidates = [
        candidate
        for candidate in result.root_cause_candidates
        if "image deployment failure" in candidate.cause
    ]

    assert candidates
    assert any(
        "ImagePullBackOff" in evidence
        for evidence in candidates[0].evidence
    )

def test_correlate_oomkilled():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceServiceDown",
                service="cart-service",
                severity="critical",
            )
        ],
        kubernetes={
            "pods": [
                {
                    "name": "cart-service-abc123",
                    "phase": "Running",
                    "containers": [
                        {
                            "name": "cart-service",
                            "ready": False,
                            "restart_count": 5,
                            "state": "waiting",
                            "reason": None,
                            "message": None,
                            "last_state": "terminated",
                            "last_reason": "OOMKilled",
                        }
                    ],
                }
            ]
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True

    candidates = [
        candidate
        for candidate in result.root_cause_candidates
        if "memory exhaustion" in candidate.cause
    ]

    assert candidates
    assert any(
        "OOMKilled" in evidence
        for evidence in candidates[0].evidence
    )

def test_correlate_application_error_logs():
    context = IncidentContext(
        status="firing",
        receiver="ai-diagnosis",
        incident_count=1,
        incidents=[
            Incident(
                status="firing",
                alertname="EcommerceHighErrorRate",
                service="order-service",
                severity="warning",
            )
        ],
        loki={
            "error_logs": [
                {
                    "timestamp": "2026-10-27T10:00:00Z",
                    "message": "Database connection failed",
                },
                {
                    "timestamp": "2026-10-27T10:00:01Z",
                    "message": "Exception while processing order",
                },
            ]
        },
    )

    result = correlate_evidence(context)

    assert result.consistent is True

    candidates = [
        candidate
        for candidate in result.root_cause_candidates
        if "application-level error" in candidate.cause
    ]

    assert candidates

    assert any(
        "Application error logs detected" in evidence
        for evidence in candidates[0].evidence
    )



