#!/usr/bin/env python3
"""
Example 3: Trade Finance Document Validation

Shows how trade finance platform can use Gravit to verify
document validation and payment approval.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


def main():
    print("=== Trade Finance Example ===\n")

    verifier = EpistemicVerifier()

    # Scenario: Validate shipping documents and approve payment
    intent = """
    Validate the bill of lading and commercial invoice
    for shipment #SHIP-789, then approve payment of
    250,000 EUR to the supplier.
    """

    action = {
        "type": "trade_finance",
        "action": "approve_payment",
        "shipment_id": "SHIP-789",
        "amount": 250000,
        "documents_validated": ["bill_of_lading", "invoice"],
        "missing_documents": ["certificate_of_origin"]
    }

    context = {
        "required_documents": [
            "bill_of_lading",
            "invoice",
            "certificate_of_origin",
            "packing_list"
        ],
        "max_payment": 500000,
        "counterparty_rating": "A",
        "previous_shipments": [
            {"id": "SHIP-788", "status": "completed", "on_time": True}
        ]
    }

    print("1. Processing trade finance document validation...")
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

    if not result.policy_compliant:
        print(f"\n⚠ Policy Violation Detected")

        missing = set(context["required_documents"]) - set(action["documents_validated"])
        if missing:
            print(f"   Missing required documents: {', '.join(missing)}")
            print("\n   Action required:")
            for doc in missing:
                print(f"   - Obtain {doc} from supplier")

    print("\n3. Compliance Status:")
    print(f"   MiCAR Article 74 (Transaction Monitoring): {'✓' if result.valid else '⚠'}")
    print(f"   Audit Trail Ready: {'✓' if result.valid else '⚠'}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
