import logging

from app.schemas.correlation import CorrelationResult, RootCauseCandidate
from app.schemas.diagnosis import DiagnosisState
from app.schemas.diagnosis_result import DiagnosisResult
from app.services.llm import LLMClient
from app.services.ranking import rank_root_causes

logger = logging.getLogger(__name__)


def _record_signals(state: DiagnosisState, signals: list[str]) -> DiagnosisState:
    if state.correlation is None:
        state.correlation = CorrelationResult()
    state.correlation.signals.extend(signals)
    return state


def analyze_alert(state: DiagnosisState) -> DiagnosisState:
    """Deterministic preprocessing placeholder for the incoming alert."""
    return state


def analyze_service(state: DiagnosisState) -> DiagnosisState:
    """Record Prometheus/Loki service-level signals."""
    metrics = state.service_evidence.metrics
    logs = state.service_evidence.logs
    signals: list[str] = []

    up_results = metrics.get("up", [])
    if up_results:
        value = up_results[0].get("value")
        if value and value[-1] == "0":
            signals.append("Service target is down")

    error_rate = metrics.get("error_rate")
    if isinstance(error_rate, (int, float)) and error_rate > 0.05:
        signals.append(f"Service error rate is elevated: {error_rate}")

    p95_latency = metrics.get("p95_latency")
    if isinstance(p95_latency, (int, float)) and p95_latency > 1.0:
        signals.append(f"Service p95 latency is elevated: {p95_latency}s")

    error_logs = logs.get("error_logs", [])
    if error_logs:
        signals.append(f"Service has {len(error_logs)} error log result(s)")

    return _record_signals(state, signals)


def analyze_dependency(state: DiagnosisState) -> DiagnosisState:
    """Record service-to-service and PostgreSQL dependency signals."""
    evidence = state.dependency_evidence
    signals: list[str] = []

    for dependency in evidence.services:
        service = dependency.get("service")
        healthy = dependency.get("healthy")
        if not service:
            continue

        if healthy is True:
            signals.append(f"Dependency {service} is healthy")
        elif healthy is False:
            status_code = dependency.get("status_code")
            if status_code is not None:
                signals.append(f"Dependency {service} is unhealthy (status={status_code})")
            else:
                signals.append(f"Dependency {service} is unreachable")

    postgres_healthy = (evidence.postgres or {}).get("healthy")
    if postgres_healthy is not None:
        status = "healthy" if postgres_healthy else "unhealthy"
        signals.append(f"PostgreSQL dependency is {status}")

    return _record_signals(state, signals)


def analyze_infrastructure(state: DiagnosisState) -> DiagnosisState:
    """Record Kubernetes deployment, pod and event signals."""
    evidence = state.infrastructure_evidence
    signals: list[str] = []

    deployment = evidence.deployments
    if deployment:
        desired = deployment.get("desired_replicas", 0)
        ready = deployment.get("ready_replicas", 0)
        available = deployment.get("available_replicas", 0)

        if desired == 0:
            signals.append("Kubernetes deployment has been scaled to zero replicas")
        elif ready == 0:
            signals.append("Kubernetes deployment has no ready replicas")
        elif desired > ready:
            signals.append(
                f"Kubernetes deployment has insufficient ready replicas: {ready}/{desired}"
            )

        if desired > 0 and available < desired:
            signals.append(
                f"Kubernetes deployment has insufficient available replicas: {available}/{desired}"
            )

    for pod in evidence.pods:
        pod_name = pod.get("name")
        if not pod_name:
            continue

        phase = pod.get("phase")
        if phase != "Running":
            signals.append(f"Pod {pod_name} is not running (phase={phase})")

        for container in pod.get("containers", []):
            name = container.get("name")
            if name and container.get("ready") is False:
                signals.append(f"Container {name} in pod {pod_name} is not ready")

            restarts = container.get("restart_count", 0)
            if restarts > 0:
                signals.append(
                    f"Container {name} in pod {pod_name} has restarted {restarts} time(s)"
                )

    for event in evidence.events:
        if event.get("type") == "Warning":
            reason = event.get("reason")
            signals.append(
                f"Kubernetes warning event: {reason}"
                if reason
                else "Kubernetes warning event detected"
            )

    return _record_signals(state, signals)


def analyze_os(state: DiagnosisState) -> DiagnosisState:
    """Record OS-level CPU, memory, disk and network signals."""
    evidence = state.os_evidence
    signals: list[str] = []

    # (label, data, elevated threshold); critical is always 90
    for label, data, elevated in (
        ("CPU", evidence.cpu, 75),
        ("memory", evidence.memory, 75),
        ("disk", evidence.disk, 80),
    ):
        usage = data.get("usage_percent")
        if not isinstance(usage, (int, float)):
            continue
        if usage >= 90:
            signals.append(f"OS {label} usage is critical: {usage}%")
        elif usage >= elevated:
            signals.append(f"OS {label} usage is elevated: {usage}%")

    errors = evidence.network.get("errors")
    if isinstance(errors, (int, float)) and errors > 0:
        signals.append(f"OS network errors detected: {errors}")

    return _record_signals(state, signals)


def _add_candidate(
    candidates: list[RootCauseCandidate],
    cause: str,
    evidence: list[str],
    confidence: float,
) -> None:
    if not evidence:
        return
    candidates.append(
        RootCauseCandidate(
            cause=cause,
            evidence=list(dict.fromkeys(evidence)),
            confidence=confidence,
        )
    )


def correlate(state: DiagnosisState) -> DiagnosisState:
    """Derive ranked root-cause candidates from the collected signals."""
    incident = state.incident
    correlation = state.correlation or CorrelationResult()

    if incident is None or not incident.service:
        state.correlation = correlation
        return state

    service = incident.service
    signals = correlation.signals
    candidates: list[RootCauseCandidate] = []

    def pick(predicate) -> list[str]:
        return [s for s in signals if predicate(s)]

    def add(cause: str, evidence: list[str], confidence: float) -> None:
        _add_candidate(candidates, cause, evidence, confidence)

    # 1. Service availability
    down = pick(lambda s: s in {"Service target is down", "Prometheus target is down"})
    scaled = pick(lambda s: s == "Kubernetes deployment has been scaled to zero replicas")
    no_ready = pick(lambda s: s == "Kubernetes deployment has no ready replicas")

    if scaled:
        add(f"{service} is scaled to zero replicas", down + scaled, 0.98)
    elif down and no_ready:
        add(f"{service} is unavailable", down + no_ready, 0.95)

    # 2. Error rate
    error_signals = pick(lambda s: s.startswith("Service error rate is elevated:"))
    error_logs = pick(lambda s: s.startswith("Service has ") and "error log result" in s)
    if error_signals:
        add(
            f"{service} has an elevated HTTP error rate",
            error_signals + error_logs,
            0.82 if error_logs else 0.75,
        )

    # 3. Latency
    add(
        f"{service} has elevated request latency",
        pick(lambda s: s.startswith("Service p95 latency is elevated:")),
        0.78,
    )

    # 4. Service-to-service dependencies
    for signal in pick(
        lambda s: s.startswith("Dependency ")
        and ("is unhealthy" in s or "is unreachable" in s)
    ):
        name = signal[len("Dependency "):].split(" is ", 1)[0]
        add(f"{name} is unavailable or unhealthy", [signal], 0.85)

    # 5. PostgreSQL
    add(
        "PostgreSQL is unavailable",
        pick(lambda s: s == "PostgreSQL dependency is unhealthy"),
        0.90,
    )

    # 6. Kubernetes infrastructure
    add(
        f"Kubernetes infrastructure issue affecting {service}",
        pick(lambda s: s.startswith(("Pod ", "Container ", "Kubernetes warning event:"))),
        0.80,
    )

    # 7. OS resource exhaustion
    add(
        f"OS resource exhaustion affecting {service}",
        pick(lambda s: s.startswith("OS ") and "critical" in s),
        0.85,
    )

    # 8. Generic fallback so unknown signals still yield a candidate
    if not candidates and signals:
        add(f"{service} is experiencing a service degradation or incident", signals, 0.40)

    correlation.consistent = bool(candidates)
    correlation.root_cause_candidates = rank_root_causes(candidates)
    state.correlation = correlation
    return state


async def generate_diagnosis(state: DiagnosisState) -> DiagnosisState:
    if state.incident is None:
        return state

    incident = state.incident
    correlation = state.correlation
    service = incident.service or "unknown"

    if correlation is None or not correlation.root_cause_candidates:
        state.diagnosis = "Unable to determine a root cause from the available evidence."
        state.confidence = 0.0
        state.recommendations = [
            "Collect additional metrics, logs, and Kubernetes state.",
            "Inspect recent Kubernetes events.",
        ]
        state.diagnosis_result = DiagnosisResult(
            root_cause="Unknown",
            explanation=state.diagnosis,
            affected_service=service,
            evidence=correlation.signals if correlation else [],
            confidence=0.0,
            impact=f"The impact of {service} cannot be determined from the available evidence.",
            recommendations=state.recommendations,
        )
        return state

    candidate = correlation.root_cause_candidates[0]

    logger.info("Starting LLM diagnosis for service=%s alert=%s", service, incident.alertname)
    try:
        explanation = await LLMClient().diagnose(
            incident=incident.model_dump(),
            correlation=correlation.model_dump(),
        )
        logger.info("LLM diagnosis completed successfully for service=%s", service)
    except Exception as e:
        logger.warning("LLM diagnosis failed, using deterministic fallback: %s", e, exc_info=True)
        explanation = (
            f"{candidate.cause}. "
            f"The diagnosis is supported by {len(candidate.evidence)} piece(s) of evidence."
        )

    state.diagnosis = candidate.cause
    state.confidence = candidate.score
    state.recommendations = [
        f"Inspect the {service} deployment and pod status.",
        "Inspect recent Kubernetes warning events.",
        f"Review {service} logs for related errors.",
    ]
    state.diagnosis_result = DiagnosisResult(
        root_cause=candidate.cause,
        explanation=explanation,
        affected_service=service,
        evidence=candidate.evidence,
        confidence=candidate.score,
        impact=f"The {service} service may be unavailable or degraded for users.",
        recommendations=state.recommendations,
    )
    return state