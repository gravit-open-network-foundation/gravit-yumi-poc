#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
echo "=== Deploying Gravit Verifier to $ENVIRONMENT ==="

case $ENVIRONMENT in
    dev)
        echo "Starting development environment..."
        docker-compose -f docker/docker-compose.prod.yml up --build
        ;;
    staging)
        echo "Deploying to staging..."
        docker build -t gravit/verifier:staging .
        kubectl config use-context staging
        helm upgrade --install gravit-yumi-poc ./k8s/helm/gravit-yumi-poc \
            --namespace gravit-system --create-namespace \
            --set image.tag=staging
        ;;
    production)
        echo "Deploying to production..."
        VERSION=$(git describe --tags --always)
        docker build -t gravit/verifier:$VERSION -t gravit/verifier:latest .
        helm upgrade --install gravit-yumi-poc ./k8s/helm/gravit-yumi-poc \
            --namespace gravit-system --create-namespace \
            --set image.tag=$VERSION --wait --timeout 5m
        ;;
    *)
        echo "Usage: ./scripts/deploy.sh [dev|staging|production]"
        exit 1
        ;;
esac

echo "✓ Deployment to $ENVIRONMENT complete"
