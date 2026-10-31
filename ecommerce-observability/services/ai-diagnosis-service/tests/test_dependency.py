import pytest

from app.services.dependency import DependencyClient


@pytest.mark.anyio
async def test_check_service_healthy(monkeypatch):
    class MockResponse:
        status_code = 200

        @property
        def is_success(self):
            return True

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            assert url == "http://cart-service:8000/health"
            return MockResponse()

    monkeypatch.setattr(
        "app.services.dependency.httpx.AsyncClient",
        lambda **kwargs: MockClient(),
    )

    client = DependencyClient()

    result = await client.check_service(
        service="cart-service",
        url="http://cart-service:8000",
    )

    assert result["service"] == "cart-service"
    assert result["healthy"] is True
    assert result["status_code"] == 200


@pytest.mark.anyio
async def test_check_service_unhealthy(monkeypatch):
    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            raise __import__("httpx").ConnectError(
                "connection failed"
            )

    monkeypatch.setattr(
        "app.services.dependency.httpx.AsyncClient",
        lambda **kwargs: MockClient(),
    )

    client = DependencyClient()

    result = await client.check_service(
        service="cart-service",
        url="http://cart-service:8000",
    )

    assert result["service"] == "cart-service"
    assert result["healthy"] is False
    assert result["status_code"] is None
    assert "error" in result