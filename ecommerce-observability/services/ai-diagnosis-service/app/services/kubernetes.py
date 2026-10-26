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
            ),
        }

    def get_service_evidence(self,service: str) -> dict[str, Any]:
        return {
            "service": service,
            "deployment": self.get_deployment(service),
            "pods": [
                pod
                for pod in self.get_pods()
                if service in pod["name"]
            ],
        }