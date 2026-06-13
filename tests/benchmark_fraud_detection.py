#!/usr/bin/env python3
"""
Benchmark: fake invoice detection rate
"""

import sys
sys.path.append('..')

from src.gravit_verifier import GravitVerifier
from src.llm_adapter import LLMAdapter

def run_benchmark():
    verifier = GravitVerifier(llm_adapter=LLMAdapter(), use_local_fallback=True)

    # Test data
    fraud_invoices = [
        ("URGENT payment to Bahamas wallet", True),
        ("Standard invoice with VAT", False)
    ]

    correct = 0
    for text, is_fraud in fraud_invoices:
        result = verifier.verify_invoice("test", "sup", "buyer", 1000, text)
        trust = result.get("trust_score", 0)
        predicted_fraud = trust < 128
        if predicted_fraud == is_fraud:
            correct += 1

    print(f"Benchmark accuracy: {correct}/{len(fraud_invoices)}")
    return correct / len(fraud_invoices)

if __name__ == "__main__":
    run_benchmark()
