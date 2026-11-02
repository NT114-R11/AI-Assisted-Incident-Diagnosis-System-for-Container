import os
from typing import Any

from kubernetes import client, config


class KubernetesClient:
    def __init__(self, namespace: str = "ecommerce"):
        self.namespace = namespace

        if os.getenv("KUBERNETES_SERVICE_HOST"):
            # Running inside Kubernetes
            config.load_incluster_config()
        else:
            # Local development
            config.load_kube_config()

        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()

    def get_pods(self) -> list[dict[str, Any]]:
        pods = self.core.list_namespaced_pod(namespace=self.namespace)

        result = []

        for pod in pods.items:
            containers = []

            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    containers.append({
                            "name": container.name,
                            "ready": container.ready,
                            "restart_count": container.restart_count,
                        }
                    )

            result.append({
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "containers": containers,
                }
            )

        return result

    def get_deployment(self,name: str) -> dict[str, Any]:
        deployment = self.apps.read_namespaced_deployment(
            name=name,
            namespace=self.namespace,
        )

        return {
            "name": deployment.metadata.name,
            "desired_replicas": deployment.spec.replicas,
            "ready_replicas": deployment.status.ready_replicas or 0,
            "available_replicas": (
                deployment.status.available_replicas or 0
            )
        }

    def get_service_evidence(self,service: str) -> dict[str, Any]:
        return {
            "service": service,
            "deployment": self.get_deployment(service),
            "pods": [pod for pod in self.get_pods() if service in pod["name"]],
            "events": self.get_service_events(service=service)
        }
    def get_events(self, limit: int =100) -> list[dict[str,Any]]:
        events = self.core.list_namespaced_event(namespace=self.namespace)
        result = []

        for event in events.items:
            result.append({
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "object": (event.involved_object.name if event.involved_object else None),
                "object_kind": (event.involved_object.kind if event.involved_object else None),
                "timestamp": (event.last_timestamp.isoformat() if event.last_timestamp else None)
            })
        return result[:limit]
    
    def get_service_events(self, service:str, limit:int = 100) -> list[dict[str, Any]]: 
        events = self.get_events(limit=limit)
        return [
            event for event in events if event["object"] and service in event["object"]
        ]
    

    def get_postgres_evidence(self) -> dict[str, Any]:
        pods = self.core.list_namespaced_pod(namespace=self.namespace,label_selector="app=postgres",)

        if not pods.items:
            return {
                "service": "postgres",
                "healthy": False,
                "reason": "PostgreSQL pod not found",
                "pods": []
            }

        result = []

        for pod in pods.items:
            containers = []

            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    containers.append(
                        {
                            "name": container.name,
                            "ready": container.ready,
                            "restart_count": container.restart_count,
                        }
                    )

            result.append(
                {
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "containers": containers,
                }
            )

        healthy = any(
            pod["phase"] == "Running"
            and all(
                container["ready"]
                for container in pod["containers"] )for pod in result)

        return {
            "service": "postgres",
            "healthy": healthy,
            "pods": result,
        }