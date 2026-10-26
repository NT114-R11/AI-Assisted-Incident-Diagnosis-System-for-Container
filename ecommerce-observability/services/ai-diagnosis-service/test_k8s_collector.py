from pprint import pprint

from app.services.kubernetes import KubernetesClient


k8s = KubernetesClient()

print("=" * 60)
print("ORDER SERVICE EVIDENCE")

evidence = k8s.get_service_evidence("order-service")

pprint(evidence)