# Integration Guide: Yumi × Gravit

## Overview

This guide provides step-by-step instructions for integrating Gravit trust verification into the Yumi Finance credit engine.

**Estimated time:** 2–3 days for complete integration

---

## Prerequisites

- [ ] Access to Yumi development environment
- [ ] API keys for Gravit (provided)
- [ ] Node.js 18+ or Python 3.10+ (for backend)
- [ ] Docker (optional, for local testing)

---

## Step 1: Get Gravit API Access

```bash
# Request API key from Gravit team
# They will provide:
# - GRAVIT_API_KEY
# - GRAVIT_VERIFIER_URL
```

---

## Step 2: Install Gravit SDK

### Python

```bash
pip install gravit-sdk
```

### Node.js

```bash
npm install @gravit/sdk
```

---

## Step 3: Integrate into Yumi Credit Engine

### Example: Yumi Credit API with Gravit verification (Python)

```python
# yumi_credit_engine.py
import os
from gravit_sdk import GravitVerifier

# Initialize Gravit client
gravit = GravitVerifier(
    api_key=os.getenv("GRAVIT_API_KEY"),
    base_url=os.getenv("GRAVIT_VERIFIER_URL")
)

async def issue_credit(request):
    # Step 1: Gather borrower data
    borrower_data = {
        "borrower_id": request.borrower_id,
        "amount": request.amount,
        "invoice_text": request.invoice_text,
        "credit_history": await get_credit_history(request.borrower_id)
    }

    # Step 2: Verify with Gravit
    verification = await gravit.verify_credit(
        borrower_id=borrower_data["borrower_id"],
        requested_amount=borrower_data["amount"],
        reasoning_chain=generate_reasoning(borrower_data),
        context=borrower_data
    )

    # Step 3: Make decision based on verification
    if verification.decision == "approve" and verification.trust_score >= 200:
        # Execute credit issuance
        tx_hash = await execute_credit(request)
        await store_audit_proof(verification.trace_id, tx_hash)
        return {"approved": True, "trace_id": verification.trace_id}
    else:
        return {"approved": False, "reason": verification.reason}
```

---

## Step 4: Update Smart Contract (Solidity)

```solidity
// YumiGravitAdapter.sol
interface IGravitVerifier {
    function verify(bytes calldata proof) external returns (
        bytes32 traceId,
        uint8 trustScore,
        bool allowed
    );
}

contract YumiCreditEngine {
    IGravitVerifier public gravit;
    uint8 public constant TRUST_THRESHOLD = 200;

    function issueCreditWithGravit(
        address borrower,
        uint256 amount,
        bytes calldata gravitProof
    ) external returns (bool) {
        (bytes32 traceId, uint8 trustScore, bool allowed) =
            gravit.verify(gravitProof);

        require(allowed && trustScore >= TRUST_THRESHOLD, "Gravit verification failed");

        // Issue credit
        _issueCredit(borrower, amount);

        emit CreditIssuedWithProof(borrower, amount, traceId, trustScore);
        return true;
    }
}
```

---

## Step 5: Test Integration

```bash
# Run test suite
python tests/test_yumi_integration.py

# Expected output:
# ✓ Credit approval with valid invoice: PASSED
# ✓ Credit rejection with fake invoice: PASSED
# ✓ Audit trail generation: PASSED
```

---

## Step 6: Deploy to Staging

```bash
# Set environment variables
export GRAVIT_API_KEY=your_staging_key
export GRAVIT_VERIFIER_URL=https://staging.gravit.network

# Deploy
docker-compose -f docker/docker-compose.prod.yml up -d
```

---

## Support

For integration questions:

- Gravit team: integration@gravit.network
- Technical documentation: [docs.gravit.network](https://docs.gravit.network/)
