from app.schemas.correlation import RootCauseCandidate
from app.services.ranking import (
    calculate_candidate_score,
    rank_root_causes,
)


def test_calculate_candidate_score():
    candidate = RootCauseCandidate(
        cause="order-service is unavailable",
        evidence=[
            "Service target is down",
            "Kubernetes deployment has no ready replicas",
            "Pod is not ready"
        ],
        confidence=0.95)

    score = calculate_candidate_score(candidate)
    assert score == 0.81


def test_rank_root_causes():
    candidates = [
        RootCauseCandidate(
            cause="Dependency cart-service is unreachable",
            evidence=[
                "Dependency cart-service is unreachable",
            ],
            confidence=0.85,
        ),
        RootCauseCandidate(
            cause="order-service is unavailable",
            evidence=[
                "Service target is down",
                "Kubernetes deployment has no ready replicas",
                "Pod is not ready",
            ],
            confidence=0.95,
        ),
    ]

    ranked = rank_root_causes(candidates)

    assert ranked[0].cause == ("order-service is unavailable")
    assert ranked[1].cause == ("Dependency cart-service is unreachable")
    assert (ranked[0].score> ranked[1].score)