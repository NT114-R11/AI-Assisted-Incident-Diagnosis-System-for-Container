from typing import Any
import httpx

class DependencyClient:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    async def check_service(self, service: str, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{url.rstrip('/')}/health")
            
            return {
                "service": service,
                "healthy": response.is_success,
                "status_code": response.status_code,
                "url": url
            }
        except httpx.RequestError as exc:
            return {
                "service": service,
                "healthy": False,
                "status_code": None,
                "url": url,
                "error": str(exc)
            }

    async def check_dependencies(self, dependencies: dict[str, Any])-> list[dict[str,Any]]:
        results = []

        for service, url in dependencies.items():
            result = await self.check_service(service=service, url=url)
            results.append(result)
        
        return results

    async def collect_dependency_evidence(self, service: str, dependencies: dict[str, str]) -> dict[str, Any]:
        service_results = await self.check_dependencies(dependencies)

        return {
            "service": service,
            "dependencies": service_results,
        }