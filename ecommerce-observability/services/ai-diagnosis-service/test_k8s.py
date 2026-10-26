from kubernetes import client, config


config.load_kube_config()

v1 = client.CoreV1Api()

pods = v1.list_namespaced_pod(namespace="ecommerce")

apps = client.AppsV1Api()
deployment = apps.read_namespaced_deployment(
    name="order-service",
    namespace="ecommerce",
)

for pod in pods.items:
    print("=" * 60)
    print(f"Pod: {pod.metadata.name}")
    print(f"Phase: {pod.status.phase}")
    
    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            print(f"Container: {container.name}")
            print(f"   Ready: {container.ready}")
            print(f"   Restart count: {container.restart_count}")


print("=" * 60)
print("Deployment:", deployment.metadata.name)
print("Desired replicas:", deployment.spec.replicas)
print("Ready replicas:", deployment.status.ready_replicas)
print("Available replicas:", deployment.status.available_replicas)