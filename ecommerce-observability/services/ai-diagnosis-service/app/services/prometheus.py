import os
from typing import Any

import httpx


class PrometheusClient:
    def __init__(self, base_url: str | None = None,):
        self.base_url = (
            base_url
            or os.getenv("PROMETHEUS_URL")
            or "http://prometheus:9090"
        ).rstrip("/")

    async def query(self, promql: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/v1/query"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"query": promql},
            )

        response.raise_for_status()

        payload = response.json()

        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus query failed: {payload}"
            )

        return payload["data"]["result"]

    async def get_service_status(self,service: str,) -> list[dict[str, Any]]:
        return await self.query(
            f'up{{job="ecommerce-services",service="{service}"}}'
        )

    async def get_request_rate(self,service: str,) -> list[dict[str, Any]]:
        return await self.query(
            f'''
            sum(
                rate(
                    http_requests_total{{
                        job="ecommerce-services",
                        service="{service}"
                    }}[5m]
                )
            )
            '''
        )

    async def get_error_rate(self,service: str,) -> list[dict[str, Any]]:
        return await self.query(
            f'''
            (
                sum(
                    rate(
                        http_requests_total{{
                            job="ecommerce-services",
                            service="{service}",
                            status=~"4xx|5xx"
                        }}[5m]
                    )
                )
                /
                sum(
                    rate(
                        http_requests_total{{
                            job="ecommerce-services",
                            service="{service}"
                        }}[5m]
                    )
                )
            )
            '''
        )

    async def get_p95_latency(self,service: str,) -> list[dict[str, Any]]:
        return await self.query(
            f'''
            histogram_quantile(
                0.95,
                sum by (le) (
                    rate(
                        http_request_duration_highr_seconds_bucket{{
                            job="ecommerce-services",
                            service="{service}"
                        }}[5m]
                    )
                )
            )
            '''
        )

    async def collect_service_evidence(self,service: str,) -> dict[str, Any]:
        return {
            "service": service,
            "up": await self.get_service_status(service),
            "request_rate": await self.get_request_rate(service),
            "error_rate": await self.get_error_rate(service),
            "p95_latency": await self.get_p95_latency(service),
        }