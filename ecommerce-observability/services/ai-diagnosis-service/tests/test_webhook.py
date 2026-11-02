from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.routers import webhook


client = TestClient(app)


def test_alertmanager_webhook(monkeypatch):
    async def mock_prometheus(service: str):
        return {
            "service": service,
            "up": [
                {
                    "metric": {"service": service},
                    "value": [1, "0"],
                }
            ],
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
            "events": [],
        }

    def mock_postgres():
        return {
            "service": "postgres",
            "healthy": True,
            "pods": [],
        }

    fake_llm = MagicMock()
    fake_llm.diagnose = AsyncMock(
        return_value=(
            "The order-service is unavailable because its "
            "Kubernetes deployment has no ready replicas."
        )
    )

    monkeypatch.setattr(
        webhook.prometheus,
        "collect_service_evidence",
        mock_prometheus,
    )

    monkeypatch.setattr(
        webhook.loki,
        "collect_service_evidence",
        mock_loki,
    )

    monkeypatch.setattr(
        webhook.kubernetes,
        "get_service_evidence",
        mock_kubernetes,
    )

    monkeypatch.setattr(
        webhook.kubernetes,
        "get_postgres_evidence",
        mock_postgres,
    )

    monkeypatch.setattr(
        "app.graph.nodes.LLMClient",
        lambda: fake_llm,
    )

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

    assert data["status"] == "diagnosed"

    diagnosis = data["diagnosis"]

    assert diagnosis["root_cause"] == "order-service is unavailable"
    assert diagnosis["affected_service"] == "order-service"
    assert diagnosis["confidence"] > 0.0

    assert "Service target is down" in diagnosis["evidence"]

    assert (
        "Kubernetes deployment has no ready replicas"
        in diagnosis["evidence"]
    )

    assert len(diagnosis["recommendations"]) == 3

    assert (
        diagnosis["explanation"]
        == (
            "The order-service is unavailable because its "
            "Kubernetes deployment has no ready replicas."
        )
    )

    fake_llm.diagnose.assert_awaited_once()