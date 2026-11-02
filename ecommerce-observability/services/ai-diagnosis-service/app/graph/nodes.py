from app.schemas.diagnosis import DiagnosisState
from app.schemas.correlation import (CorrelationResult, RootCauseCandidate)
from app.services.ranking import rank_root_causes
from app.schemas.diagnosis_result import DiagnosisResult
from app.services.llm import LLMClient
import logging
logger = logging.getLogger(__name__)

def analyze_alert(state: DiagnosisState) -> DiagnosisState:
    """
    Analyze the incoming incident alert.

    This node performs deterministic preprocessing only.
    """
    if state.incident is None:
        return state

    return state

def analyze_service(state: DiagnosisState) -> DiagnosisState:
    """
    Analyze application/service-level evidence.

    This node inspects metrics and logs collected from
    Prometheus and Loki and records deterministic signals
    for later correlation.
    """
    evidence = state.service_evidence
    metrics = evidence.metrics
    logs = evidence.logs
    signals: list[str] = []

    # Prometheus: target availability
    up_results = metrics.get("up", [])

    if up_results:
        value = up_results[0].get("value")

        if value and value[-1] == "0":
            signals.append("Service target is down")

    # Prometheus: error rate
    error_rate = metrics.get("error_rate")

    if isinstance(error_rate, (int, float)) and error_rate > 0:
        signals.append(f"Service error rate is elevated: {error_rate}")

    # Prometheus: p95 latency
    p95_latency = metrics.get("p95_latency")

    if isinstance(p95_latency, (int, float)) and p95_latency > 1.0:
        signals.append(f"Service p95 latency is elevated: {p95_latency}s")

    # Loki: application errors
    error_logs = logs.get("error_logs", [])
    if error_logs:
        signals.append(f"Service has {len(error_logs)} error log result(s)")

    # Store deterministic service signals in correlation.
    if state.correlation is None:
        from app.schemas.correlation import CorrelationResult
        state.correlation = CorrelationResult()

    state.correlation.signals.extend(signals)
    return state

def analyze_dependency(state: DiagnosisState) -> DiagnosisState:
    """
    Analyze service-to-service and PostgreSQL dependencies.

    This node records deterministic dependency signals.
    It does not determine the final root cause.
    """
    evidence = state.dependency_evidence

    signals: list[str] = []

    # Service-to-service dependencies
    for dependency in evidence.services:
        service = dependency.get("service")
        healthy = dependency.get("healthy")

        if not service:
            continue

        if healthy is False:
            status_code = dependency.get("status_code")

            if status_code is not None:
                signals.append(
                    f"Dependency {service} is unhealthy "
                    f"(status={status_code})")
            else:
                signals.append(f"Dependency {service} is unreachable")

        elif healthy is True:
            signals.append(f"Dependency {service} is healthy")
    # PostgreSQL
    postgres = evidence.postgres

    if postgres:
        postgres_healthy = postgres.get("healthy")

        if postgres_healthy is False:
            signals.append("PostgreSQL dependency is unhealthy")
        elif postgres_healthy is True:
            signals.append("PostgreSQL dependency is healthy")

    if state.correlation is None:
        from app.schemas.correlation import CorrelationResult

        state.correlation = CorrelationResult()
    state.correlation.signals.extend(signals)
    return state

def analyze_infrastructure(state: DiagnosisState,) -> DiagnosisState:
    """
    Analyze Kubernetes infrastructure evidence.

    This node performs deterministic analysis of:
    - pods
    - deployments
    - Kubernetes events

    It records infrastructure signals for later correlation.
    """
    evidence = state.infrastructure_evidence
    signals: list[str] = []
    # Analyze deployment
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
                f"Kubernetes deployment has insufficient ready replicas: {ready}/{desired}")

        if desired > 0 and available < desired:
            signals.append(
                f"Kubernetes deployment has insufficient available replicas: {available}/{desired}")

    # Analyze pods
    for pod in evidence.pods:
        pod_name = pod.get("name")
        phase = pod.get("phase")

        if not pod_name:
            continue

        if phase != "Running":
            signals.append(
                f"Pod {pod_name} is not running "
                f"(phase={phase})")

        for container in pod.get("containers", []):
            container_name = container.get("name")
            ready = container.get("ready")
            restart_count = container.get("restart_count", 0)

            if container_name and ready is False:
                signals.append(
                    f"Container {container_name} in pod "
                    f"{pod_name} is not ready")

            if restart_count > 0:
                signals.append(
                    f"Container {container_name} in pod "
                    f"{pod_name} has restarted "
                    f"{restart_count} time(s)")

    # Analyze Kubernetes events
    for event in evidence.events:
        event_type = event.get("type")
        reason = event.get("reason")

        if event_type == "Warning":
            if reason:
                signals.append(f"Kubernetes warning event: {reason}")
            else:
                signals.append("Kubernetes warning event detected")

    if state.correlation is None:
        from app.schemas.correlation import CorrelationResult

        state.correlation = CorrelationResult()
    state.correlation.signals.extend(signals)
    return state

def analyze_os(state: DiagnosisState) -> DiagnosisState:
    """
    Analyze operating-system evidence collected from
    Node Exporter / Prometheus.

    This node performs deterministic analysis of:
    - CPU
    - memory
    - disk
    - network
    """
    evidence = state.os_evidence
    signals: list[str] = []

    # CPU
    cpu = evidence.cpu
    usage_percent = cpu.get("usage_percent")
    if isinstance(usage_percent, (int, float)):
        if usage_percent >= 90:
            signals.append(f"OS CPU usage is critical: {usage_percent}%")
        elif usage_percent >= 75:
            signals.append(f"OS CPU usage is elevated: {usage_percent}%")

    # Memory
    memory = evidence.memory
    usage_percent = memory.get("usage_percent")
    if isinstance(usage_percent, (int, float)):
        if usage_percent >= 90:
            signals.append(f"OS memory usage is critical: {usage_percent}%")
        elif usage_percent >= 75:
            signals.append(f"OS memory usage is elevated: {usage_percent}%")

    # Disk
    disk = evidence.disk
    usage_percent = disk.get("usage_percent")
    if isinstance(usage_percent, (int, float)):
        if usage_percent >= 90:
            signals.append(f"OS disk usage is critical: {usage_percent}%")
        elif usage_percent >= 80:
            signals.append(f"OS disk usage is elevated: {usage_percent}%")

    # Network
    network = evidence.network
    errors = network.get("errors")
    if isinstance(errors, (int, float)) and errors > 0:
        signals.append(f"OS network errors detected: {errors}")

    if state.correlation is None:
        from app.schemas.correlation import CorrelationResult
        state.correlation = CorrelationResult()
    state.correlation.signals.extend(signals)
    return state

def correlate(state: DiagnosisState) -> DiagnosisState:
    """
    Correlate signals across all evidence layers.
    This node performs deterministic cross-layer reasoning.

    The purpose is to:
    - determine whether evidence is consistent,
    - identify root-cause candidates,
    - attach supporting evidence,
    - assign a deterministic confidence score.
    """

    incident = state.incident
    correlation = state.correlation
    if correlation is None:
        correlation = CorrelationResult()
    if incident is None or not incident.service:
        state.correlation = correlation
        return state

    service = incident.service
    signals = correlation.signals
    candidates: list[RootCauseCandidate] = []

    # Service unavailable

        # Service unavailable

    service_down = (
        "Service target is down" in signals
        or "Prometheus target is down" in signals)

    deployment_scaled_to_zero = (
        "Kubernetes deployment has been scaled to zero replicas"
        in signals)

    deployment_unavailable = (
        "Kubernetes deployment has no ready replicas"
        in signals)

    # Case 1: Deployment was explicitly scaled to zero.
    if deployment_scaled_to_zero:
        evidence = [
            signal
            for signal in signals
            if signal in {
                "Service target is down",
                "Prometheus target is down",
                "Kubernetes deployment has been scaled to zero replicas",
            }
        ]

        candidates.append(
            RootCauseCandidate(
                cause=f"{service} is scaled to zero replicas",
                evidence=evidence,
                confidence=0.98,
            )
        )

    # Case 2: Service is down while deployment expects replicas.
    elif service_down and deployment_unavailable:
        evidence = [
            signal
            for signal in signals
            if signal in {
                "Service target is down",
                "Prometheus target is down",
                "Kubernetes deployment has no ready replicas",
            }
        ]

        candidates.append(
            RootCauseCandidate(
                cause=f"{service} is unavailable",
                evidence=evidence,
                confidence=0.95,
            )
        )



    # Dependency failure

    unhealthy_dependencies = [
        signal
        for signal in signals
        if signal.startswith("Dependency ")
        and (
            "is unhealthy" in signal
            or "is unreachable" in signal
        )
    ]

    if unhealthy_dependencies:
        for signal in unhealthy_dependencies:
            candidates.append(
                RootCauseCandidate(
                    cause=signal,
                    evidence=[signal],
                    confidence=0.85,
                )
            )

    # PostgreSQL failure

    postgres_unhealthy = (
        "PostgreSQL dependency is unhealthy"
        in signals)

    if postgres_unhealthy:
        candidates.append(
            RootCauseCandidate(
                cause="PostgreSQL is unavailable",
                evidence=[
                    "PostgreSQL dependency is unhealthy"
                ],
                confidence=0.90)
        )

    # Infrastructure failure

    infrastructure_signals = [
        signal
        for signal in signals
        if (
            signal.startswith("Pod ")
            or signal.startswith("Container ")
            or signal.startswith("Kubernetes warning event:")
        )
    ]

    if infrastructure_signals:
        candidates.append(
            RootCauseCandidate(
                cause=(
                    f"Kubernetes infrastructure issue "
                    f"affecting {service}"
                ),
                evidence=infrastructure_signals,
                confidence=0.80,
            )
        )

    # OS resource exhaustion
    os_signals = [
        signal
        for signal in signals
        if signal.startswith("OS ")
    ]

    critical_os_signals = [signal for signal in os_signals if "critical" in signal]
    if critical_os_signals:
        candidates.append(
            RootCauseCandidate(
                cause=(
                    f"OS resource exhaustion affecting "
                    f"{service}"
                ),
                evidence=critical_os_signals,
                confidence=0.85)
        )

    # Determine consistency
    correlation.consistent = len(candidates) > 0
    correlation.root_cause_candidates = rank_root_causes(candidates)
    state.correlation = correlation
    return state



async def generate_diagnosis(state: DiagnosisState) -> DiagnosisState:
    if state.incident is None:
        return state

    incident = state.incident
    correlation = state.correlation

    if correlation is None or not correlation.root_cause_candidates:
        state.diagnosis = ("Unable to determine a root cause from the available evidence.")
        state.confidence = 0.0
        state.recommendations = [
            "Collect additional metrics, logs, and Kubernetes state.",
            "Inspect recent Kubernetes events."]

        state.diagnosis_result = DiagnosisResult(
            root_cause="Unknown",
            explanation=state.diagnosis,
            affected_service=incident.service or "unknown",
            evidence=correlation.signals if correlation else [],
            confidence=0.0,
            impact=(
                f"The impact of {incident.service or 'the affected service'} "
                "cannot be determined from the available evidence."
            ),
            recommendations=state.recommendations
        )

        return state

    candidate = correlation.root_cause_candidates[0]
    service = incident.service or "unknown"

    logger.info("Starting LLM diagnosis for service=%s alert=%s",service,incident.alertname)
    try:
        llm_client = LLMClient()

        llm_result = await llm_client.diagnose(
            incident=incident.model_dump(),
            correlation=correlation.model_dump())
        logger.info("LLM diagnosis completed successfully for service=%s",service)
    except Exception as e:

        logger.warning("LLM diagnosis failed, using deterministic fallback: %s",e, exc_info=True)

        llm_result = (
            f"{candidate.cause}. "
            f"The diagnosis is supported by "
            f"{len(candidate.evidence)} piece(s) of evidence.")

    state.diagnosis = candidate.cause
    state.confidence = candidate.score

    state.recommendations = [
        f"Inspect the {service} deployment and pod status.",
        "Inspect recent Kubernetes warning events.",
        f"Review {service} logs for related errors.",
    ]

    state.diagnosis_result = DiagnosisResult(
        root_cause=candidate.cause,
        explanation=llm_result,
        affected_service=service,
        evidence=candidate.evidence,
        confidence=candidate.score,
        impact=(
            f"The {service} service may be unavailable or degraded for users."
        ),
        recommendations=state.recommendations,
    )

    return state