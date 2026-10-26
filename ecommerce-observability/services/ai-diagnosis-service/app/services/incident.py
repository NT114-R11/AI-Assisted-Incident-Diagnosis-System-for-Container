from app.schemas.alertmanager import AlertmanagerWebhook
from app.schemas.incident import Incident, IncidentContext


def process_alert(payload: AlertmanagerWebhook) -> IncidentContext:
    incidents = []

    for alert in payload.alerts:
        incidents.append(
            Incident(
                status=alert.status,
                alertname=alert.labels.get("alertname"),
                service=alert.labels.get("service"),
                severity=alert.labels.get("severity"),
                summary=alert.annotations.get("summary"),
                description=alert.annotations.get("description"),
                starts_at=alert.startsAt,
            )
        )

    return IncidentContext(
        status=payload.status,
        receiver=payload.receiver,
        incident_count=len(incidents),
        incidents=incidents,
    )