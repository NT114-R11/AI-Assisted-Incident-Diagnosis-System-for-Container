from fastapi.testclient import TestClient

from app.main import app
from app.routers import webhook


client = TestClient(app)


def test_alertmanager_webhook():
    async def mock_prometheus(service: str):
        return {
            "service": service,
            "up": [{"metric": {"service": service}, "value": [1, "0"]}],
        }

    async def mock_loki(service: str):
        return {
            "service": service,
            "logs": [],
            "error_logs": [],
        }

    def mock_kubernetes(service: str):
        return {
            "service": service,
            "deployment": {
                "name": service,
                "desired_replicas": 1,
                "ready_replicas": 0,
                "available_replicas": 0,
            },
            "pods": [],
        }

    webhook.prometheus.collect_service_evidence = mock_prometheus
    webhook.loki.collect_service_evidence = mock_loki
    webhook.kubernetes.get_service_evidence = mock_kubernetes

    payload = {
        "version": "4",
        "status": "firing",
        "receiver": "ai-diagnosis",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "EcommerceOrderServiceMissing",
                    "service": "order-service",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "Order Service target is missing",
                    "description": (
                        "order-service has no active Prometheus target."
                    ),
                },
                "startsAt": "2026-10-24T15:31:05.436Z",
            }
        ],
    }

    response = client.post(
        "/webhook/alertmanager",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "firing"
    assert data["receiver"] == "ai-diagnosis"
    assert data["incident_count"] == 1

    incident = data["incidents"][0]

    assert incident["alertname"] == "EcommerceOrderServiceMissing"
    assert incident["service"] == "order-service"
    assert incident["severity"] == "critical"

    assert data["prometheus"]["service"] == "order-service"
    assert data["loki"]["service"] == "order-service"
    assert data["kubernetes"]["service"] == "order-service"

    assert data["diagnosis"] is None
    assert data["correlation"] is not None

    assert data["correlation"]["consistent"] is True

    assert (
        "Prometheus target is down"
        in data["correlation"]["signals"]
    )

    assert (
        "Kubernetes deployment has no ready replicas"
        in data["correlation"]["signals"]
    )

    assert data["correlation"]["root_cause_candidates"] == [
        "order-service is unavailable"
    ]