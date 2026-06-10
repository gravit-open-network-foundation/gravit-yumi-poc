#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
echo "=== Deploying Gravit Verifier to $ENVIRONMENT ==="

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    source .env.$ENVIRONMENT
else
    echo "⚠ Warning: .env.$ENVIRONMENT not found, using defaults"
fi

case $ENVIRONMENT in
    dev)
        echo "Starting development environment..."
        docker-compose -f docker/docker-compose.yml up --build
        ;;

    staging)
        echo "Deploying to staging..."
        # Build images
        docker build -t gravit/verifier:staging .

        # Push to registry
        docker tag gravit/verifier:staging $REGISTRY/gravit/verifier:staging
        docker push $REGISTRY/gravit/verifier:staging

        # Deploy to k8s
        kubectl config use-context staging
        helm upgrade --install gravit-yumi-poc ./k8s/helm/gravit-yumi-poc \
            --namespace gravit-system \
            --create-namespace \
            --set image.tag=staging \
            --set config.logLevel=debug
        ;;

    production)
        echo "Deploying to production..."
        # Build with version tag
        VERSION=$(git describe --tags --always)
        docker build -t gravit/verifier:$VERSION -t gravit/verifier:latest .

        # Push to registry
        docker tag gravit/verifier:$VERSION $REGISTRY/gravit/verifier:$VERSION
        docker tag gravit/verifier:latest $REGISTRY/gravit/verifier:latest
        docker push $REGISTRY/gravit/verifier:$VERSION
        docker push $REGISTRY/gravit/verifier:latest

        # Deploy to k8s with rollback strategy
        kubectl config use-context production

        # Backup current deployment
        kubectl get deployment gravit-yumi-verifier -n gravit-system -o yaml > backup.yaml || true

        # Deploy
        helm upgrade --install gravit-yumi-poc ./k8s/helm/gravit-yumi-poc \
            --namespace gravit-system \
            --create-namespace \
            --set image.tag=$VERSION \
            --set config.logLevel=info \
            --wait \
            --timeout 5m
        ;;

    *)
        echo "Unknown environment: $ENVIRONMENT"
        echo "Usage: ./scripts/deploy.sh [dev|staging|production]"
        exit 1
        ;;
esac

echo "✓ Deployment to $ENVIRONMENT complete"
