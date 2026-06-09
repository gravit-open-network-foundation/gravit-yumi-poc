# Deployment Guide: Gravit × Yumi PoC

## Local Development (Docker)

```bash
# Clone repository
git clone https://github.com/GravitOpenNetwork/gravit-yumi-poc
cd gravit-yumi-poc

# Copy environment variables
cp .env.example .env

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Verify services
curl http://localhost:8080/health

# Run demo
python examples/04_yumi_integration.py
```

## Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace gravit-yumi

# Apply configmap
kubectl apply -f k8s/configmap.yaml -n gravit-yumi

# Apply secrets (create from .env)
kubectl create secret generic gravit-secrets --from-env-file=.env -n gravit-yumi

# Deploy
kubectl apply -f k8s/deployment.yaml -n gravit-yumi
kubectl apply -f k8s/service.yaml -n gravit-yumi

# Check status
kubectl get pods -n gravit-yumi
```

---

## Production Recommendations

| Component   | Recommendation                         |
|:-----------:|:--------------------------------------|
| Replicas    | Minimum 3 for high availability        |
| Resources   | 4 GB RAM, 2 CPU cores per pod         |
| Database    | PostgreSQL for audit trail storage    |
| Monitoring  | Prometheus + Grafana                  |
| Alerting    | PagerDuty integration                 |
| Backup      | Daily audit proof backups             |

---

## Environment Configuration

| Variable             | Production Value                                 |
|:--------------------:|:-------------------------------------------------|
| ENVIRONMENT          | production                                       |
| LOG_LEVEL            | WARN                                             |
| GRAVIT_VERIFIER_URL  | https://api.gravit.network/v1/verify             |
| REPLICAS             | 3                                                |

---

## Health Check Endpoints

| Endpoint | Purpose             |
|:--------:|:--------------------|
| /health  | Liveness probe      |
| /ready   | Readiness probe     |
| /metrics | Prometheus metrics  |

