#!/usr/bin/env python3
"""
Yumi Finance Integration Demo – Complete End-to-End Example
Demonstrates how Yumi would integrate Gravit verification
"""

import sys
import json
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.append('..')

from src.gravit_verifier import GravitVerifier, TrustScore
from src.yumi_adapter import YumiGravitAdapter, YumiCreditRequest


def demo_legitimate_invoice():
    """Case 1: Legitimate invoice – should be approved"""

    print("\n" + "=" * 70)
    print("CASE 1: Legitimate Trade Invoice")
    print("=" * 70)

    invoice_text = """
    INVOICE #INV-2026-0421
    Date: 2026-06-01
    Due: 2026-07-01

    Supplier: Precision Manufacturing GmbH, Munich
    Buyer: Automotive Components AG, Stuttgart

    Items:
    - 250 units Gearbox P/N 4472-A @ €420 = €105,000
    - 150 units Hydraulic Pump P/N 8831-B @ €890 = €133,500
    - 300 units Control Module P/N 2210-C @ €175 = €52,500

    Total: €291,000
    VAT (19%): €55,290
    Grand Total: €346,290

    Payment Terms: Net 30
    Bank: Deutsche Bank, IBAN: DE89 3704 0044 0532 0130 00
    """

    request = YumiCreditRequest(
        borrower_id="Precision_Manufacturing",
        requested_amount=346290,
        invoice_text=invoice_text,
        credit_history={"loans_taken": 12, "repayment_rate": 100},
        industry="manufacturing"
    )

    adapter = YumiGravitAdapter(min_trust_score=TrustScore.TRUSTED)

    print("Processing credit request...")
    start = time.time()
    result = adapter.process_credit_request(request)
    elapsed = (time.time() - start) * 1000

    print(f"\nResult:")
    print(f"  Approved: {result['approved']}")
    print(f"  Decision: {result['decision']}")
    print(f"  Trust Score: {result['trust_score']}/255")
    print(f"  Time: {elapsed:.0f}ms")
    print(f"  Trace ID: {result['trace_id'][:32]}...")

    return result


def demo_fraudulent_invoice():
    """Case 2: Fraudulent invoice – should be rejected"""

    print("\n" + "=" * 70)
    print("CASE 2: Fraudulent Invoice (Red Flags)")
    print("=" * 70)

    invoice_text = """
    INVOICE #INV-999-URGENT
    Date: 2026-06-08

    Supplier: CryptoTrade Solutions Ltd, Bahamas
    Buyer: [REDACTED]

    Items:
    - AI Consulting Services: €250,000
    - Blockchain Development: €375,000
    - Strategic Advisory: €200,000

    Total: €825,000

    Payment: USDC to wallet 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
    Note: URGENT – Payment required within 24 hours
    """

    request = YumiCreditRequest(
        borrower_id="CryptoTrade",
        requested_amount=825000,
        invoice_text=invoice_text,
        credit_history={"loans_taken": 0, "repayment_rate": 0},
        industry="cryptocurrency"
    )

    adapter = YumiGravitAdapter(min_trust_score=TrustScore.TRUSTED)

    print("Processing credit request...")
    start = time.time()
    result = adapter.process_credit_request(request)
    elapsed = (time.time() - start) * 1000

    print(f"\nResult:")
    print(f"  Approved: {result['approved']}")
    print(f"  Decision: {result['decision']}")
    print(f"  Trust Score: {result['trust_score']}/255")
    print(f"  Time: {elapsed:.0f}ms")
    print(f"  Trace ID: {result['trace_id'][:32]}...")

    if not result['approved']:
        print(f"  Reason: {result.get('reason', 'Trust score below threshold')}")

    return result


def demo_summary():
    """Print summary comparison"""

    print("\n" + "=" * 70)
    print("DEMO SUMMARY: Gravit × Yumi Integration")
    print("=" * 70)

    legit = demo_legitimate_invoice()
    fraud = demo_fraudulent_invoice()

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print(f"✓ Legitimate invoice: {'APPROVED' if legit['approved'] else 'REJECTED'}")
    print(f"✓ Fraudulent invoice: {'APPROVED' if fraud['approved'] else 'REJECTED'}")

    if legit['approved'] and not fraud['approved']:
        print("\n✅ PoC SUCCESSFUL: Gravit correctly distinguishes legitimate from fraudulent invoices")
    else:
        print("\n⚠️ Review results – unexpected outcome")

    print("\nNext steps for Yumi Finance:")
    print("  1. Integrate Gravit verifier into credit API")
    print("  2. Deploy to staging environment")
    print("  3. Run A/B test with real invoices")
    print("  4. Prepare investor demo")


if __name__ == "__main__":
    demo_summary()
