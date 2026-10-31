from fastapi import APIRouter

from app.schemas.alertmanager import AlertmanagerWebhook
from app.services.incident import process_alert
from app.services.prometheus import PrometheusClient
from app.services.loki import LokiClient
from app.services.kubernetes import KubernetesClient
from app.services.correlation import correlate_evidence


router = APIRouter(
    prefix="/webhook",
    tags=["webhook"],
)

prometheus = PrometheusClient()
loki = LokiClient()
kubernetes = KubernetesClient()


@router.post("/alertmanager")
async def alertmanager_webhook(payload: AlertmanagerWebhook):
    incident = process_alert(payload)

    service = None

    if incident.incidents:
        service = incident.incidents[0].service

    if service:
        incident.prometheus = (await prometheus.collect_service_evidence(service))

        incident.loki = (await loki.collect_service_evidence(service))

        incident.kubernetes = (kubernetes.get_service_evidence(service))

        incident.correlation = correlate_evidence(incident)

    return incident