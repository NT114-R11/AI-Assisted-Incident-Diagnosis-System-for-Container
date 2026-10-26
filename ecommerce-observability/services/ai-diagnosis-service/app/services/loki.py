import os
from typing import Any

import httpx


class LokiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (
            base_url
            or os.getenv("LOKI_URL")
            or "http://loki:3100"
        ).rstrip("/")

    async def query_range(self,logql: str,start: int | None = None,end: int | None = None,limit: int = 100,) -> list[dict[str, Any]]:
        url = f"{self.base_url}/loki/api/v1/query_range"

        params: dict[str, Any] = {
            "query": logql,
            "limit": limit,
            "direction": "backward",
        }

        if start is not None:
            params["start"] = start

        if end is not None:
            params["end"] = end

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError(f"Loki query failed: {payload}")

        return payload["data"]["result"]

    async def get_service_logs(self,service: str,limit: int = 100,) -> list[dict[str, Any]]:
        logql = f'{{namespace="ecommerce", service_name="{service}"}}'

        return await self.query_range(
            logql=logql,
            limit=limit,
        )

    async def get_service_error_logs(self,service: str,limit: int = 100,) -> list[dict[str, Any]]:
        logql = (
            f'{{namespace="ecommerce", service_name="{service}"}} '
            '|~ "(?i)(error|exception|traceback|failed)"'
        )

        return await self.query_range(
            logql=logql,
            limit=limit,
        )

    async def collect_service_evidence(self,service: str,) -> dict[str, Any]:
        logs = await self.get_service_logs(service)
        error_logs = await self.get_service_error_logs(service)

        return {
            "service": service,
            "logs": logs,
            "error_logs": error_logs,
        }