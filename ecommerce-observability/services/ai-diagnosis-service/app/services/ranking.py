from app.schemas.correlation import RootCauseCandidate


def calculate_candidate_score(candidate: RootCauseCandidate) -> float:
    """
    Calculate a deterministic priority score for a root-cause
    candidate.

    The score is intentionally simple and explainable.
    It is not a statistical probability.
    """

    evidence_count = len(candidate.evidence)

    evidence_score = min(
        evidence_count / 5,1.0)
    confidence_score = candidate.confidence

    score = (
        confidence_score * 0.6
        + evidence_score * 0.4)

    return round(score, 3)


def rank_root_causes(candidates: list[RootCauseCandidate],) -> list[RootCauseCandidate]:
    """
    Rank root-cause candidates from strongest to weakest.
    """

    for candidate in candidates:
        candidate.score = calculate_candidate_score(candidate)

    return sorted(
        candidates,
        key=lambda candidate: candidate.score,
        reverse=True,
    )