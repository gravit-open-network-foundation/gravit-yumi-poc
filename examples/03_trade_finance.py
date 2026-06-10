#!/usr/bin/env python3
"""Example 3: Trade Finance Document Validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verifier import EpistemicVerifier
from src.models import VerificationRequest


def main():
    print("=== Trade Finance Example ===\n")

    verifier = EpistemicVerifier()

    intent = """
    Validate documents and approve payment for shipment #SHIP-789.
    """

    action = {
        "type": "trade_finance",
        "action": "approve_payment",
        "shipment_id": "SHIP-789",
        "amount": 250000,
        "documents_validated": ["bill_of_lading", "invoice"]
    }

    context = {
        "required_documents": ["bill_of_lading", "invoice", "certificate_of_origin"],
        "max_payment": 500000
    }

    request = VerificationRequest(intent=intent, action=action, context=context)
    result = verifier.verify(request)

    print(f"Valid: {result.valid}")
    print(f"Policy Compliant: {result.policy_compliant}")

    if not result.policy_compliant:
        missing = set(context["required_documents"]) - set(action["documents_validated"])
        print(f"Missing documents: {', '.join(missing)}")


if __name__ == "__main__":
    main()
