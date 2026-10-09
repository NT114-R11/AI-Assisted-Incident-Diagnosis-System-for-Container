import uuid
from typing import Any


def get_request_id(request: Any) -> str:
    state = getattr(request, "state", None)
    request_id = getattr(state, "request_id", None)
    if request_id:
        return str(request_id)

    headers = getattr(request, "headers", {})
    forwarded = headers.get("X-Request-ID") if headers else None
    if forwarded:
        return str(forwarded)

    return str(uuid.uuid4())


def build_forward_headers(request: Any) -> dict[str, str]:
    return {"X-Request-ID": get_request_id(request)}
