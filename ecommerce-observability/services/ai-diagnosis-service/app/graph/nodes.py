from app.schemas.diagnosis import DiagnosisState


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

        if desired > 0 and ready == 0:
            signals.append( "Kubernetes deployment has no ready replicas")

        if desired > ready:
            signals.append(
                f"Kubernetes deployment has insufficient "
                f"ready replicas: {ready}/{desired}")

        if desired > available:
            signals.append(
                f"Kubernetes deployment has insufficient "
                f"available replicas: {available}/{desired}")

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