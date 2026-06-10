#!/bin/bash
set -e

echo "=== Gravit Epistemic Verifier - End-to-End Tests ==="

# Start services
docker-compose -f docker/docker-compose.prod.yml up -d
sleep 10

# Health check
curl -f http://localhost:8080/health || exit 1
echo "✓ Health check passed"

# Test valid transaction
echo "Test 1: Valid transaction"
RESPONSE=$(curl -s -X POST http://localhost:8080/v1/verify \
    -H "Content-Type: application/json" \
    -d '{"intent": "Send 100 EURAU to Alice", "action": {"type": "transfer", "to": "Alice", "amount": 100}, "context": {"balance": 550}}')

if echo "$RESPONSE" | grep -q '"valid":true'; then
    echo "✓ Test 1 passed"
else
    echo "✗ Test 1 failed"
    exit 1
fi

# Test semantic mismatch
echo "Test 2: Semantic mismatch"
RESPONSE=$(curl -s -X POST http://localhost:8080/v1/verify \
    -H "Content-Type: application/json" \
    -d '{"intent": "Check balance", "action": {"type": "transfer", "to": "Malory", "amount": 10000}, "context": {"balance": 500}}')

if echo "$RESPONSE" | grep -q '"valid":false'; then
    echo "✓ Test 2 passed"
else
    echo "✗ Test 2 failed"
    exit 1
fi

# Cleanup
docker-compose -f docker/docker-compose.prod.yml down
echo "=== All E2E Tests Passed ==="
