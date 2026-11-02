from fastapi import APIRouter

from app.graph.workflow import diagnosis_graph
from app.schemas.alertmanager import AlertmanagerWebhook
from app.schemas.diagnosis import DiagnosisState
from app.services.dependency import DependencyClient
from app.services.dependencies import SERVICE_DEPENDENCIES
from app.services.incident import process_alert
from app.services.kubernetes import KubernetesClient
from app.services.loki import LokiClient
from app.services.prometheus import PrometheusClient
from app.services.telegram import TelegramNotifier

import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

prometheus = PrometheusClient()
loki = LokiClient()
telegram_notifier = TelegramNotifier()
kubernetes = KubernetesClient()
dependency_client = DependencyClient()


@router.post("/alertmanager")
async def alertmanager_webhook(payload: AlertmanagerWebhook):
    incident_context = process_alert(payload)

    if not incident_context.incidents:
        return {
            "status": "ignored",
            "reason": "No incidents found",
        }

    incident = incident_context.incidents[0]
    service = incident.service

    if not service:
        return {
            "status": "ignored",
            "reason": "Incident has no service",
        }

    # Handle resolved alerts separately.
    # A resolved incident does not need to run the diagnosis pipeline again.
    if payload.status == "resolved":
        try:
            await telegram_notifier.send_resolved(
                service=service,
                alertname=incident.alertname,
            )
        except Exception:
            logger.exception(
                "Failed to send Telegram resolved notification"
            )

        return {
            "status": "resolved",
            "service": service,
            "alertname": incident.alertname,
        }

    # Firing alert -> collect evidence and run diagnosis.
    service_evidence = await prometheus.collect_service_evidence(service)

    loki_evidence = await loki.collect_service_evidence(service)

    kubernetes_evidence = kubernetes.get_service_evidence(service)

    dependencies = SERVICE_DEPENDENCIES.get(service, {})

    dependency_evidence = (
        await dependency_client.collect_dependency_evidence(
            service=service,
            dependencies=dependencies,
        )
    )

    postgres_evidence = kubernetes.get_postgres_evidence()

    state = DiagnosisState(
        incident=incident,
        service_evidence={
            "metrics": service_evidence,
            "logs": loki_evidence,
        },
        dependency_evidence={
            "services": dependency_evidence.get(
                "dependencies",
                [],
            ),
            "postgres": postgres_evidence,
        },
        infrastructure_evidence={
            "pods": kubernetes_evidence.get(
                "pods",
                [],
            ),
            "deployments": kubernetes_evidence.get(
                "deployment",
                {},
            ),
            "events": kubernetes_evidence.get(
                "events",
                [],
            ),
        },
    )

    result = await diagnosis_graph.ainvoke(state)
    diagnosis = result.get("diagnosis_result")

    if diagnosis is None:
        return {
            "status": "failed",
            "reason": "Diagnosis could not be generated",
        }

    try:
        await telegram_notifier.send_diagnosis(diagnosis)
    except Exception:
        logger.exception(
            "Failed to send Telegram notification"
        )

    return {
        "status": "diagnosed",
        "diagnosis": diagnosis.model_dump(),
    }
