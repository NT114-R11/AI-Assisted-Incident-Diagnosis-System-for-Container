import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

for service in ("cart-service", "product-service", "order-service"):
    sys.path.insert(0, str(ROOT / "services" / service))

from app.request_context import build_forward_headers


def test_build_forward_headers_uses_existing_request_id():
    request = SimpleNamespace(
        headers={"X-Request-ID": "trace-123"},
        state=SimpleNamespace(request_id="trace-123"),
    )

    assert build_forward_headers(request) == {"X-Request-ID": "trace-123"}


def test_build_forward_headers_generates_when_missing():
    request = SimpleNamespace(headers={}, state=SimpleNamespace())

    headers = build_forward_headers(request)

    assert headers["X-Request-ID"]
