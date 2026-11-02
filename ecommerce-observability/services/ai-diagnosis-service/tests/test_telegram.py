from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.schemas.diagnosis_result import DiagnosisResult
from app.services.telegram import TelegramNotifier


@pytest.mark.asyncio
async def test_send_message():
    notifier = TelegramNotifier()

    with patch("app.services.telegram.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value

        response = MagicMock() 
        mock_instance.post = AsyncMock(return_value=response)
        await notifier.send_message("Test Telegram notification")
        mock_instance.post.assert_awaited_once()
        response.raise_for_status.assert_called_once() 
        args, kwargs = mock_instance.post.call_args

        assert "sendMessage" in args[0]
        assert kwargs["json"]["chat_id"] == "8424464735"
        assert kwargs["json"]["text"] == "Test Telegram notification"


@pytest.mark.asyncio
async def test_send_diagnosis():
    notifier = TelegramNotifier()

    diagnosis = DiagnosisResult(
        root_cause="order-service is scaled to zero replicas",
        explanation="The deployment has zero replicas.",
        affected_service="order-service",
        evidence=[
            "Kubernetes deployment has been scaled to zero replicas",
        ],
        confidence=0.668,
        impact="Order service is unavailable.",
        recommendations=[
            "Scale order-service back up.",
        ],
    )

    with patch("app.services.telegram.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value

        response = MagicMock()
        mock_instance.post = AsyncMock(return_value=response)

        await notifier.send_diagnosis(diagnosis)

        mock_instance.post.assert_awaited_once()
        response.raise_for_status.assert_called_once()

        _, kwargs = mock_instance.post.call_args
        message = kwargs["json"]["text"]

        assert "INCIDENT DETECTED" in message
        assert "order-service" in message
        assert "scaled to zero replicas" in message
        assert "66.8%" in message

