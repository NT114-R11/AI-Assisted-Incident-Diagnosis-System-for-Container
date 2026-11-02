from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import LLMClient


def test_build_prompt():
    incident = {
        "alertname": "EcommerceOrderServiceMissing",
        "service": "order-service",
        "severity": "critical",
        "summary": "Order Service target is missing",
    }

    correlation = {
        "signals": [
            "Service target is down",
            "Kubernetes deployment has been scaled to zero replicas",
        ],
        "root_cause_candidates": [
            {
                "cause": "order-service is scaled to zero replicas",
                "evidence": [
                    "Kubernetes deployment has been scaled to zero replicas",
                ],
                "confidence": 0.98,
                "score": 0.668,
            }
        ],
    }

    prompt = LLMClient._build_prompt(
        incident=incident,
        correlation=correlation,
    )

    assert "order-service" in prompt
    assert "EcommerceOrderServiceMissing" in prompt
    assert "Kubernetes deployment has been scaled to zero replicas" in prompt
    assert "Do not invent evidence." in prompt


@pytest.mark.asyncio
async def test_diagnose():
    fake_message = MagicMock()
    fake_message.content = (
        "The order-service is scaled to zero replicas. "
        "This is supported by the Kubernetes deployment evidence."
    )

    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=fake_message)
    ]

    with patch("app.services.llm.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=fake_response)

        mock_openai.return_value = mock_client
        client = LLMClient()
        incident = {
            "alertname": "EcommerceOrderServiceMissing",
            "service": "order-service",
            "severity": "critical",
            "summary": "Order Service target is missing"
        }

        correlation = {
            "signals": [
                "Service target is down",
                "Kubernetes deployment has been scaled to zero replicas",
            ],
            "root_cause_candidates": [
                {
                    "cause": "order-service is scaled to zero replicas",
                    "evidence": [
                        "Kubernetes deployment has been scaled to zero replicas",
                    ],
                    "confidence": 0.98,
                    "score": 0.668,
                }
            ]
        }

        result = await client.diagnose(incident=incident,correlation=correlation)

        assert result == fake_message.content
        mock_client.chat.completions.create.assert_awaited_once()
        call_kwargs = (mock_client.chat.completions.create.await_args.kwargs)

        assert call_kwargs["model"] == client.model
        messages = call_kwargs["messages"]
        assert any(
            "order-service" in message["content"]
            for message in messages)

        assert any(
            "scaled to zero replicas" in message["content"]
            for message in messages)