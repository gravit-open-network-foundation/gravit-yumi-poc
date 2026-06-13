#!/bin/bash
# ============================================================================
# Unified Deployment Script for Gravit Epistemic Verifier
# Usage: ./deploy.sh [dev|staging|production]
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

show_help() {
    echo "Usage: ./deploy.sh [dev|staging|production]"
    echo ""
    echo "Commands:"
    echo "  dev         Local Docker Compose deployment"
    echo "  staging     Kubernetes staging deployment"
    echo "  production  Kubernetes production deployment with Helm"
}

# Check environment argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: Environment argument required${NC}"
    show_help
    exit 1
fi

# Load .env file properly (fix for special characters)
load_env() {
    if [ -f .env ]; then
        set -a
        source .env
        set +a
        echo -e "${GREEN}✓ Loaded .env file${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
        if [ "$1" = "production" ]; then
            echo -e "${RED}Error: Production requires .env file${NC}"
            exit 1
        fi
    fi
}

ENV=$1

case $ENV in
    dev)
        echo -e "${GREEN}🚀 Deploying to DEVELOPMENT environment${NC}"
        load_env "dev"

        # Create .env for docker-compose if missing
        if [ ! -f .env ]; then
            cp .env.example .env
            echo -e "${YELLOW}Created .env from .env.example - edit for custom configuration${NC}"
        fi

        docker-compose -f docker/docker-compose.yml up --build -d

        echo -e "${GREEN}✅ Development deployment complete${NC}"
        echo "API: http://localhost:8080"
        echo "Health: curl http://localhost:8080/health"
        echo "Docs: http://localhost:8080/docs"
        echo "Grafana: http://localhost:3000 (admin/${GRAFANA_PASSWORD:-admin123})"
        echo "Prometheus: http://localhost:9090"
        ;;

    staging)
        echo -e "${YELLOW}🚀 Deploying to STAGING environment${NC}"
        load_env "staging"

        if ! command -v kubectl &> /dev/null; then
            echo -e "${RED}Error: kubectl not found${NC}"
            exit 1
        fi

        kubectl create namespace gravit-staging --dry-run=client -o yaml | kubectl apply -f -

        # Create secret from .env
        kubectl create secret generic gravit-secrets \
            --from-env-file=.env \
            -n gravit-staging \
            --dry-run=client -o yaml | kubectl apply -f -

        kubectl apply -f k8s/configmap.yaml -n gravit-staging
        kubectl apply -f k8s/deployment.yaml -n gravit-staging
        kubectl apply -f k8s/service.yaml -n gravit-staging

        kubectl rollout status deployment/gravit-verifier -n gravit-staging --timeout=300s

        echo -e "${GREEN}✅ Staging deployment complete${NC}"
        ;;

    production)
        echo -e "${GREEN}🚀 Deploying to PRODUCTION environment${NC}"
        load_env "production"

        if ! command -v helm &> /dev/null; then
            echo -e "${RED}Error: helm not found${NC}"
            exit 1
        fi

        # Validate required variables
        if [ -z "$GRAVIT_API_KEY" ]; then
            echo -e "${RED}Error: GRAVIT_API_KEY must be set in .env for production${NC}"
            exit 1
        fi

        kubectl create namespace gravit-production --dry-run=client -o yaml | kubectl apply -f -

        helm upgrade --install gravit-verifier ./k8s/helm \
            --namespace gravit-production \
            --set environment=production \
            --set replicaCount=3 \
            --set resources.requests.memory="2Gi" \
            --set resources.requests.cpu="1000m" \
            --set secrets.apiKey="$GRAVIT_API_KEY" \
            --wait --timeout 10m

        echo -e "${GREEN}✅ Production deployment complete${NC}"
        echo "Monitor: kubectl get pods -n gravit-production -w"
        ;;

    *)
        echo -e "${RED}Error: Unknown environment '$ENV'${NC}"
        show_help
        exit 1
        ;;
esac
