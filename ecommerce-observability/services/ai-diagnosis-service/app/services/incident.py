from app.schemas.alertmanager import AlertmanagerWebhook


def process_alert(payload: AlertmanagerWebhook) -> dict:
    incidents = []

    for alert in payload.alerts:
        incidents.append(
            {
                "status": alert.status,
                "alertname": alert.labels.get("alertname"),
                "service": alert.labels.get("service"),
                "severity": alert.labels.get("severity"),
                "summary": alert.annotations.get("summary"),
                "description": alert.annotations.get("description"),
                "starts_at": alert.startsAt,
            }
        )

    return {
        "status": payload.status,
        "receiver": payload.receiver,
        "incident_count": len(incidents),
        "incidents": incidents,
    }