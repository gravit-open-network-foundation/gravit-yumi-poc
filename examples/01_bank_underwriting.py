#!/usr/bin/env python3
"""Example 1: Bank Underwriting with Epistemic Verification."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


def main():
    print("=== Bank Underwriting Example ===\n")

    verifier = EpistemicVerifier()

    intent = """
    Underwrite a loan of 500,000 EUR to SME Corp
    with 750,000 EUR real estate collateral.
    """

    action = {
        "type": "loan_underwriting",
        "approved": True,
        "amount": 500000,
        "borrower": "SME_Corp",
        "collateral_value": 750000,
        "ltv": 0.667,
        "interest_rate": 0.08
    }

    context = {
        "bank_policies": {"max_ltv": 0.70},
        "borrower_rating": "BBB",
        "current_exposure": 1200000
    }

    request = VerificationRequest(intent=intent, action=action, context=context)
    result = verifier.verify(request)

    print(f"Valid: {result.valid}")
    print(f"Semantic Score: {result.semantic_score:.2f}")
    print(f"Policy Compliant: {result.policy_compliant}")

    if result.valid:
        print("\n✓ Loan underwriting decision VERIFIED")
    else:
        print(f"\n✗ Rejected: {result.failure_reason}")


if __name__ == "__main__":
    main()
