from app.schemas.incident import IncidentContext
from app.schemas.correlation import CorrelationResult, RootCauseCandidate


def _add_candidate(candidates: list[RootCauseCandidate],cause: str,evidence: list[str],confidence: float) -> None:
    if not evidence:
        return

    candidates.append(
        RootCauseCandidate(
            cause=cause,
            evidence=list(dict.fromkeys(evidence)),
            confidence=confidence,
        )
    )


def _last_value(results: list[dict]) -> str | None:
    if not results:
        return None

    value = results[0].get("value")
    if isinstance(value, list) and value:
        return str(value[-1])

    return None

def _get_kubernetes_failure_signals(kubernetes: dict) -> list[str]:
    signals = []

    pods = kubernetes.get("pods", [])

    for pod in pods:
        pod_name = pod.get("name", "unknown-pod")

        for container in pod.get("containers", []):
            reason = container.get("reason")
            last_reason = container.get("last_reason")

            if reason == "CrashLoopBackOff":
                signals.append(
                    f"Pod {pod_name} container {container.get('name')} "
                    "is in CrashLoopBackOff"
                )

            if reason == "ImagePullBackOff":
                signals.append(
                    f"Pod {pod_name} container {container.get('name')} "
                    "is in ImagePullBackOff"
                )

            if reason == "ErrImagePull":
                signals.append(
                    f"Pod {pod_name} container {container.get('name')} "
                    "failed to pull the container image"
                )

            if reason == "OOMKilled" or last_reason == "OOMKilled":
                signals.append(
                    f"Pod {pod_name} container {container.get('name')} "
                    "was terminated because of OOMKilled"
                )

    return signals

def _get_application_error_signals(loki: dict) -> list[str]:
    signals = []

    error_logs = loki.get("error_logs", [])

    if not error_logs:
        return signals

    signals.append(
        f"Application error logs detected: {len(error_logs)} error entries"
    )

    return signals

def correlate_evidence(context: IncidentContext) -> CorrelationResult:
    """
    Correlate the evidence available in IncidentContext.

    This helper mirrors the generic diagnosis strategy used by the
    LangGraph correlation node. It is intentionally based on evidence
    categories rather than one specific incident scenario.
    """
    if not context.incidents:
        return CorrelationResult()

    incident = context.incidents[0]
    service = incident.service

    if not service:
        return CorrelationResult()

    signals: list[str] = []
    candidates: list[RootCauseCandidate] = []

    prometheus = context.prometheus or {}
    loki = context.loki or {}
    kubernetes = context.kubernetes or {}

    # Collect signals: Loki
    application_error_signals = _get_application_error_signals(loki)
    signals.extend(application_error_signals)

    # Collect signals: Prometheus
    up = prometheus.get("up", [])
    if _last_value(up) == "0":
        signals.append("Prometheus target is down")

    error_rate = prometheus.get("error_rate")
    if isinstance(error_rate, (int, float)) and error_rate > 0.05:
        signals.append(f"Service error rate is elevated: {error_rate}")

    p95_latency = prometheus.get("p95_latency")
    if isinstance(p95_latency, (int, float)) and p95_latency > 1.0:
        signals.append(f"Service p95 latency is elevated: {p95_latency}s")

    # Collect signals: Kubernetes
    kubernetes_failure_signals = _get_kubernetes_failure_signals(kubernetes)
    signals.extend(kubernetes_failure_signals)

    deployment = kubernetes.get("deployment")
    if deployment:
        desired = deployment.get("desired_replicas")
        ready = deployment.get("ready_replicas")

        if desired == 0:
            signals.append("Kubernetes deployment has been scaled to zero replicas")
        elif desired is not None and desired > 0 and ready == 0:
            signals.append("Kubernetes deployment has no ready replicas")

    # Availability
    if "Kubernetes deployment has been scaled to zero replicas" in signals:
        evidence = [
            signal
            for signal in signals
            if signal in {
                "Prometheus target is down",
                "Kubernetes deployment has been scaled to zero replicas",
            }
        ]
        _add_candidate(
            candidates,
            f"{service} is scaled to zero replicas",
            evidence,
            0.98,
        )
    elif (
        "Prometheus target is down" in signals
        and "Kubernetes deployment has no ready replicas" in signals
    ):
        _add_candidate(
            candidates,
            f"{service} is unavailable",
            [
                "Prometheus target is down",
                "Kubernetes deployment has no ready replicas",
            ],
            0.95,
        )

    # Application errors
    if application_error_signals:
        _add_candidate(
            candidates,
            f"{service} has an application-level error",
            application_error_signals,
            0.80,
        )

    # Kubernetes container failures
    crashloop_signals = [
        signal
        for signal in kubernetes_failure_signals
        if "CrashLoopBackOff" in signal
    ]
    if crashloop_signals:
        _add_candidate(
            candidates,
            f"{service} has a container restart failure",
            crashloop_signals,
            0.90,
        )

    image_pull_signals = [
        signal
        for signal in kubernetes_failure_signals
        if "ImagePullBackOff" in signal
        or "failed to pull the container image" in signal
    ]
    if image_pull_signals:
        _add_candidate(
            candidates,
            f"{service} has a container image deployment failure",
            image_pull_signals,
            0.90,
        )

    oom_signals = [
        signal
        for signal in kubernetes_failure_signals
        if "OOMKilled" in signal
    ]
    if oom_signals:
        _add_candidate(
            candidates,
            f"{service} is experiencing memory exhaustion",
            oom_signals,
            0.92,
        )

    # Error rate
    error_signals = [
        signal
        for signal in signals
        if signal.startswith("Service error rate is elevated:")
    ]
    if error_signals:
        _add_candidate(
            candidates,
            f"{service} has an elevated HTTP error rate",
            error_signals,
            0.75,
        )

    # Latency
    latency_signals = [
        signal
        for signal in signals
        if signal.startswith("Service p95 latency is elevated:")
    ]
    if latency_signals:
        _add_candidate(
            candidates,
            f"{service} has elevated request latency",
            latency_signals,
            0.78,
        )

    return CorrelationResult(
        consistent=bool(candidates),
        signals=signals,
        root_cause_candidates=candidates,
    )


def calculate_candidate_score(candidate):
    evidence_count = len(candidate.evidence)
    evidence_score = min(evidence_count / 5, 1.0)
    confidence_score = candidate.confidence

    score = confidence_score * 0.6 + evidence_score * 0.4

    return round(score, 3)


def rank_root_causes(candidates):
    for candidate in candidates:
        candidate.score = calculate_candidate_score(candidate)

    return sorted(
        candidates,
        key=lambda candidate: candidate.score,
        reverse=True,
    )

