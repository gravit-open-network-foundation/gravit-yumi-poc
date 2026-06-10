#!/usr/bin/env python3
"""
Example 2: DeFi Lending Recommendation with Epistemic Verification

Shows how a DeFi protocol can use Gravit to verify lending position
recommendations before execution.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


def main():
    print("=== DeFi Lending Example ===\n")

    verifier = EpistemicVerifier()

    # Scenario: Agent recommends a lending position
    intent = """
    Recommend a stablecoin lending position on Aave
    with low risk profile. Prefer AA-rated pools
    and APY > 3%.
    """

    action = {
        "type": "defi_lending",
        "protocol": "Aave",
        "asset": "USDC",
        "amount": 100000,
        "pool_rating": "AA",
        "expected_apy": 0.035,
        "liquidation_threshold": 0.85
    }

    context = {
        "risk_tolerance": "conservative",
        "allowed_protocols": ["Aave", "Compound", "Spark"],
        "min_pool_rating": "A",
        "min_apy": 0.02,
        "max_position": 500000,
        "current_positions": [
            {"protocol": "Compound", "asset": "DAI", "amount": 50000}
        ]
    }

    print("1. Processing DeFi lending recommendation...")
    request = VerificationRequest(
        intent=intent,
        action=action,
        context=context
    )

    result = verifier.verify(request)

    print(f"\n2. Verification Result:")
    print(f"   Valid: {result.valid}")
    print(f"   Semantic Score: {result.semantic_score:.2f}")
    print(f"   Policy Compliant: {result.policy_compliant}")

    if result.valid:
        print("\n✓ Lending recommendation VERIFIED")
        print("\n   Position details:")
        print(f"   - Protocol: {action['protocol']}")
        print(f"   - Asset: {action['asset']}")
        print(f"   - Amount: ${action['amount']:,}")
        print(f"   - Expected APY: {action['expected_apy']*100:.1f}%")
    else:
        print("\n✗ Recommendation REJECTED")

        # Suggest alternatives
        if not result.policy_compliant:
            print("   Policy violation detected. Consider:")
            if action['pool_rating'] < context['min_pool_rating']:
                print(f"   - Use pool with rating >= {context['min_pool_rating']}")
            if action['expected_apy'] < context['min_apy']:
                print(f"   - Find APY >= {context['min_apy']*100:.1f}%")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
