from app.schemas.alertmanager import AlertmanagerWebhook
from app.services.incident import process_alert


def test_process_alert():
    payload = AlertmanagerWebhook(
        status="firing",
        receiver="ai-diagnosis",
        alerts=[
            {
                "status": "firing",
                "labels": {
                    "alertname": "EcommerceOrderServiceMissing",
                    "service": "order-service",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "Order Service target is missing",
                    "description": "order-service has no active Prometheus target.",
                },
                "startsAt": "2026-10-24T15:31:05.436Z",
            }
        ],
    )

    context = process_alert(payload)

    assert context.status == "firing"
    assert context.receiver == "ai-diagnosis"

    assert context.incident_count == 1
    assert len(context.incidents) == 1

    incident = context.incidents[0]

    assert incident.status == "firing"
    assert incident.alertname == "EcommerceOrderServiceMissing"
    assert incident.service == "order-service"
    assert incident.severity == "critical"
    assert incident.summary == "Order Service target is missing"
    assert incident.description == (
        "order-service has no active Prometheus target."
    )

    assert context.prometheus is None
    assert context.loki is None
    assert context.kubernetes is None
    assert context.diagnosis is None


def test_process_alert_multiple_alerts():
    payload = AlertmanagerWebhook(
        status="firing",
        receiver="ai-diagnosis",
        alerts=[
            {
                "status": "firing",
                "labels": {
                    "alertname": "EcommerceOrderServiceMissing",
                    "service": "order-service",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "Order Service target is missing",
                },
            },
            {
                "status": "firing",
                "labels": {
                    "alertname": "EcommerceProductServiceHighErrorRate",
                    "service": "product-service",
                    "severity": "warning",
                },
                "annotations": {
                    "summary": "Product Service error rate is high",
                },
            },
        ],
    )

    context = process_alert(payload)

    assert context.incident_count == 2
    assert len(context.incidents) == 2

    assert context.incidents[0].service == "order-service"
    assert context.incidents[1].service == "product-service"


def test_process_alert_empty_alerts():
    payload = AlertmanagerWebhook(
        status="resolved",
        receiver="ai-diagnosis",
        alerts=[],
    )

    context = process_alert(payload)

    assert context.status == "resolved"
    assert context.receiver == "ai-diagnosis"
    assert context.incident_count == 0
    assert context.incidents == []

    assert context.prometheus is None
    assert context.loki is None
    assert context.kubernetes is None
    assert context.diagnosis is None