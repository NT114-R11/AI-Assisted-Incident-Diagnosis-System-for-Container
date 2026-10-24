# Triển khai observability

## Prometheus
```
k8s/observability/prometheus/prometheus.yaml
```

## Grafana

```
kubectl apply -k k8s/observability/grafana/
```
- Verify
```
kubectl get pods -n ecommerce -l app=grafana
```