#!/usr/bin/env python3
"""Example 2: DeFi Lending Recommendation with Epistemic Verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


def main():
    print("=== DeFi Lending Example ===\n")

    verifier = EpistemicVerifier()

    intent = """
    Recommend a stablecoin lending position on Aave
    with low risk profile. Prefer AA-rated pools.
    """

    action = {
        "type": "defi_lending",
        "protocol": "Aave",
        "asset": "USDC",
        "amount": 100000,
        "pool_rating": "AA",
        "expected_apy": 0.035
    }

    context = {
        "risk_tolerance": "conservative",
        "allowed_protocols": ["Aave", "Compound"],
        "min_pool_rating": "A",
        "min_apy": 0.02
    }

    request = VerificationRequest(intent=intent, action=action, context=context)
    result = verifier.verify(request)

    print(f"Valid: {result.valid}")
    print(f"Semantic Score: {result.semantic_score:.2f}")

    if result.valid:
        print("\n✓ Lending recommendation VERIFIED")
    else:
        print(f"\n✗ Rejected: {result.failure_reason}")


if __name__ == "__main__":
    main()
