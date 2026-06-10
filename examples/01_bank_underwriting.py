#!/usr/bin/env python3
"""
Example 1: Bank Underwriting with Epistemic Verification

Shows how a bank can use Gravit to verify loan underwriting decisions
before approval.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest
from src.audit_proof import AuditProofGenerator


def main():
    print("=== Bank Underwriting Example ===\n")

    # Initialize verifier
    verifier = EpistemicVerifier(
        semantic_threshold=0.75,
        adversarial_threshold=0.2
    )

    # Scenario: Underwrite a business loan
    intent = """
    Underwrite a loan of 500,000 EUR to SME Corp
    with 750,000 EUR real estate collateral.
    Loan-to-value ratio should not exceed 70%.
    """

    action = {
        "type": "loan_underwriting",
        "approved": True,
        "amount": 500000,
        "borrower": "SME_Corp",
        "collateral_value": 750000,
        "ltv": 0.667,
        "interest_rate": 0.08,
        "term_months": 12
    }

    context = {
        "bank_policies": {
            "max_ltv": 0.70,
            "min_borrower_rating": "BB",
            "max_exposure": 2000000
        },
        "borrower_rating": "BBB",
        "current_exposure": 1200000,
        "regulatory_jurisdiction": "EU_MiCAR"
    }

    print("1. Processing loan underwriting request...")
    request = VerificationRequest(
        intent=intent,
        action=action,
        context=context
    )

    # Verify
    result = verifier.verify(request)

    print(f"\n2. Verification Result:")
    print(f"   Valid: {result.valid}")
    print(f"   Semantic Score: {result.semantic_score:.2f}")
    print(f"   Policy Compliant: {result.policy_compliant}")
    print(f"   Adversarial Risk: {result.adversarial_risk:.2f}")

    if result.valid:
        print("\n✓ Loan underwriting decision VERIFIED")

        # Generate audit proof
        proof_gen = AuditProofGenerator()
        proof = proof_gen.generate(
            request=request,
            result=result,
            agent_id="bank_underwriting_agent_01",
            reasoning_chain=[
                "Calculated LTV: 500k/750k = 0.667",
                "Policy max LTV is 0.70 → within limit",
                "Borrower rating BBB meets minimum BB",
                "Current exposure + new loan = 1.7M < 2M limit"
            ]
        )

        print("\n3. Audit Proof Generated (ERC-8004-GT):")
        print(f"   Proof ID: {proof['proof_id']}")
        print(f"   Timestamp: {proof['timestamp']}")
        print(f"   Merkle Root: {proof['lineage_commitment']['merkle_root'][:16]}...")

        # Store proof for compliance
        import json
        with open("loan_proof.json", "w") as f:
            json.dump(proof, f, indent=2)
        print("\n   ✓ Proof saved to loan_proof.json")

    else:
        print("\n✗ Loan decision REJECTED")
        print(f"   Reason: {result.failure_reason}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
