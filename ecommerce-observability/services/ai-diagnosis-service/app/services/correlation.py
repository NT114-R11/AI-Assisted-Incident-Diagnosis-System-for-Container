from app.schemas.incident import IncidentContext
from app.schemas.correlation import CorrelationResult


def correlate_evidence(context: IncidentContext,) -> CorrelationResult:
    signals: list[str] = []
    root_causes: list[str] = []

    if not context.incidents:
        return CorrelationResult()

    incident = context.incidents[0]
    service = incident.service

    if not service:
        return CorrelationResult()

    # ========================Prometheus evidence =============================
    prometheus = context.prometheus

    if prometheus:
        up = prometheus.get("up", [])

        if up:
            value = up[0].get("value")

            if value and value[-1] == "0":
                signals.append(
                    "Prometheus target is down"
                )

    #========================== Kubernetes evidence===================
   
    kubernetes = context.kubernetes

    if kubernetes:
        deployment = kubernetes.get("deployment", {})

        desired = deployment.get("desired_replicas", 0)
        ready = deployment.get("ready_replicas", 0)

        if desired > 0 and ready == 0:
            signals.append(
                "Kubernetes deployment has no ready replicas"
            )

   
    # ===================Correlation =====================
    if len(signals) >= 2:
        consistent = True

        root_causes.append(
            f"{service} is unavailable"
        )
    else:
        consistent = False

    return CorrelationResult(
        consistent=consistent,
        signals=signals,
        root_cause_candidates=root_causes,
    )